"""
Bask — main entry: web UI, optional REPL, reminder poller, TTS worker.

Run from repo root:
  python -m bask.main --config config.yaml
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import uvicorn

from bask.audio import play_wav_async, record_wav, synthesize_openai_speech, synthesize_piper, transcribe_openai_whisper
from bask.calendar import calendar_service, list_today_events
from bask.camera.snapshot import capture_jpeg
from bask.config import AppConfig
from bask.llm import complete_chat, load_system_prompt
from bask.reminders import add_reminder, connect, delete_reminder, due_reminders, init_schema
from bask.secrets_store import load_profiles
from bask.ui import UIState, create_display
from bask.web import build_app

log = logging.getLogger("bask")
BASK_PKG = Path(__file__).resolve().parent


def _project_root(config_path: Path) -> Path:
    return config_path.resolve().parent


async def tts_worker(
    queue: asyncio.Queue[str],
    cfg: AppConfig,
    openai_key: str,
    tmp_dir: Path,
) -> None:
    while True:
        text = await queue.get()
        try:
            out = tmp_dir / "tts_out.wav"
            if cfg.tts.provider == "openai" and openai_key:
                await synthesize_openai_speech(
                    api_key=openai_key,
                    text=text,
                    voice=cfg.tts.openai_voice,
                    out_path=out,
                )
            elif cfg.tts.provider == "piper":
                await synthesize_piper(text, cfg.tts.piper_binary, cfg.tts.piper_voice, out)
            else:
                log.info("TTS disabled; would say: %s", text[:200])
                continue
            await play_wav_async(out, cfg.audio.output_device)
        except Exception:
            log.exception("TTS playback failed")
        finally:
            queue.task_done()


async def reminder_poller(
    cfg: AppConfig,
    conn,
    tts_queue: asyncio.Queue[str],
    interval_sec: float = 20.0,
) -> None:
    while True:
        await asyncio.sleep(interval_sec)
        try:
            for r in due_reminders(conn):
                msg = f"Pengingat: {r.title}"
                await tts_queue.put(msg)
                delete_reminder(conn, r.id)
        except Exception:
            log.exception("Reminder poll failed")


async def run_chat(
    cfg: AppConfig,
    project_root: Path,
    profiles_path: Path,
    user_text: str,
    image_path: Path | None,
    tts_queue: asyncio.Queue[str] | None,
    display,
) -> str:
    profiles = load_profiles(profiles_path)
    prof = profiles.active_profile()
    preset = profiles.active_model_preset
    system = load_system_prompt(BASK_PKG)
    img = image_path.read_bytes() if image_path else None
    reply = await complete_chat(
        cfg=cfg,
        profile=prof,
        llm=cfg.llm,
        preset_id=preset,
        user_text=user_text,
        system_prompt=system,
        image_bytes=img,
    )
    display.show_state(UIState.speaking, reply[:48], reply[48:96] if len(reply) > 48 else "")
    if tts_queue:
        await tts_queue.put(reply)
    return reply


def cmd_web(cfg: AppConfig, project_root: Path, profiles_path: Path) -> None:
    app = build_app(cfg, profiles_path, project_root)
    uvicorn.run(app, host=cfg.web.host, port=cfg.web.port, log_level="info")


async def cmd_repl(cfg: AppConfig, project_root: Path, profiles_path: Path) -> None:
    tmp = project_root / "data" / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    profiles = load_profiles(profiles_path)
    prof = profiles.active_profile()
    db_path = cfg.resolve_path(project_root, cfg.database_path)
    conn = connect(db_path)
    init_schema(conn)
    dump_dir = project_root / "data" / "ui_dump"
    display = create_display(
        backend=cfg.oled.backend if cfg.oled.enabled else "mock",
        width=cfg.oled.width,
        height=cfg.oled.height,
        gpio=cfg.oled.gpio,
        dump_dir=dump_dir,
    )
    tts_q: asyncio.Queue[str] = asyncio.Queue()
    tts_task = asyncio.create_task(tts_worker(tts_q, cfg, prof.openai_api_key, tmp))
    poll_task = asyncio.create_task(reminder_poller(cfg, conn, tts_q))
    print("Bask REPL — chat | foto | listen | remind ISO|judul | cal today | quit")
    try:
        while True:
            line = await asyncio.to_thread(input, "> ")
            line = line.strip()
            if not line or line.lower() == "quit":
                break
            if line.lower().startswith("chat "):
                text = line[5:].strip()
                display.show_state(UIState.thinking, "...", "")
                reply = await run_chat(cfg, project_root, profiles_path, text, None, tts_q, display)
                print(reply)
                display.show_state(UIState.idle, "Bask", "")
            elif line.lower().startswith("foto "):
                q = line[5:].strip()
                display.show_state(UIState.listening, "foto...", "")
                try:
                    jpeg, _ = capture_jpeg()
                except Exception as e:
                    print("Camera:", e)
                    continue
                p = tmp / "cap.jpg"
                p.write_bytes(jpeg)
                display.show_state(UIState.thinking, "vision", "")
                reply = await run_chat(cfg, project_root, profiles_path, q, p, tts_q, display)
                print(reply)
                display.show_state(UIState.idle, "Bask", "")
            elif line.lower() == "listen":
                if not prof.openai_api_key or cfg.stt.provider == "none":
                    print("STT needs OpenAI key and stt.provider openai_whisper_api")
                    continue
                wav = tmp / "in.wav"
                display.show_state(UIState.listening, "mic...", "")
                try:
                    record_wav(wav, seconds=4.0, device=cfg.audio.input_device, rate=cfg.audio.sample_rate)
                except Exception as e:
                    print("Record failed:", e)
                    continue
                text = await transcribe_openai_whisper(
                    api_key=prof.openai_api_key, audio_path=wav, model=cfg.stt.model
                )
                print("Heard:", text)
                display.show_state(UIState.thinking, "", "")
                await run_chat(cfg, project_root, profiles_path, text, None, tts_q, display)
                display.show_state(UIState.idle, "Bask", "")
            elif line.lower().startswith("remind "):
                rest = line[7:].strip()
                if "|" not in rest:
                    print("Format: remind 2026-06-20T15:00:00|Judul")
                    continue
                iso, title = rest.split("|", 1)
                try:
                    when = datetime.fromisoformat(iso.strip())
                except ValueError:
                    print("Invalid datetime")
                    continue
                rid = add_reminder(conn, title.strip(), when)
                print(f"Reminder #{rid} saved")
            elif line.lower() == "cal today":
                cred = cfg.resolve_path(project_root, cfg.calendar.credentials_path)
                tok = cfg.resolve_path(project_root, cfg.calendar.token_path)
                try:
                    svc = calendar_service(cred, tok)
                    evs = list_today_events(svc)
                except Exception as e:
                    print("Calendar:", e)
                    continue
                if not evs:
                    print("(no events)")
                for e in evs:
                    st = e.get("start", {}).get("dateTime") or e.get("start", {}).get("date", "")
                    print("-", st, e.get("summary", ""))
            else:
                print("Unknown command")
    finally:
        poll_task.cancel()
        tts_task.cancel()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    parser = argparse.ArgumentParser(description="Bask assistant")
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("web", help="Run settings API only")
    sub.add_parser("repl", help="Interactive text loop (dev)")
    args = parser.parse_args()
    if not args.config.exists():
        log.error("Missing %s — copy config.example.yaml", args.config)
        sys.exit(1)
    cfg = AppConfig.load(args.config)
    root = _project_root(args.config)
    os.chdir(root)
    profiles_path = root / "secrets" / "profiles.json"
    cmd = args.cmd or "repl"
    if cmd == "web":
        cmd_web(cfg, root, profiles_path)
    elif cmd == "repl":
        asyncio.run(cmd_repl(cfg, root, profiles_path))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
