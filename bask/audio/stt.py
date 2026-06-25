"""Speech-to-text via OpenAI Whisper API (multipart)."""

from __future__ import annotations

from pathlib import Path

import httpx


async def transcribe_openai_whisper(
    *,
    api_key: str,
    audio_path: Path,
    model: str = "whisper-1",
    language: str | None = None,
) -> str:
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {"model": model}
    if language:
        data["language"] = language
    files = {"file": (audio_path.name, audio_path.read_bytes(), "audio/wav")}
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, headers=headers, data=data, files=files)
        r.raise_for_status()
        js = r.json()
    return js.get("text", "").strip()
