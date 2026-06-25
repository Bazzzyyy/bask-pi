"""Text-to-speech: Piper CLI or OpenAI speech API."""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

import httpx


async def synthesize_openai_speech(
    *,
    api_key: str,
    text: str,
    voice: str = "alloy",
    out_path: Path,
) -> None:
    url = "https://api.openai.com/v1/audio/speech"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": "tts-1", "input": text, "voice": voice, "response_format": "wav"}
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(r.content)


async def synthesize_piper(text: str, piper_bin: str, voice: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    proc = await asyncio.create_subprocess_exec(
        piper_bin,
        "--model",
        voice,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE,
    )
    assert proc.stdin
    proc.stdin.write(text.encode("utf-8"))
    await proc.stdin.drain()
    proc.stdin.close()
    raw, err = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"piper failed: {err.decode(errors='replace')}")
    out_path.write_bytes(raw)


def play_wav(path: Path, output_device: str = "") -> None:
    cmd = ["aplay", "-q"]
    if output_device:
        cmd.extend(["-D", output_device])
    cmd.append(str(path))
    subprocess.run(cmd, check=True)


async def play_wav_async(path: Path, output_device: str = "") -> None:
    cmd = ["aplay", "-q"]
    if output_device:
        cmd.extend(["-D", output_device])
    cmd.append(str(path))
    proc = await asyncio.create_subprocess_exec(*cmd)
    await proc.wait()
    if proc.returncode != 0:
        raise RuntimeError("aplay failed")
