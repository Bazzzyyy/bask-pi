"""HTTP clients for OpenAI-compatible chat completions."""

from __future__ import annotations

import base64
from typing import Any

import httpx


async def chat_completion(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
    timeout: float = 120.0,
) -> str:
    """Return assistant message content text."""
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages}
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
    choice = data["choices"][0]["message"]
    return choice.get("content") or ""


def build_vision_user_message(text: str, image_bytes: bytes, mime: str = "image/jpeg") -> dict[str, Any]:
    b64 = base64.standard_b64encode(image_bytes).decode("ascii")
    return {
        "role": "user",
        "content": [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
        ],
    }


def build_text_user_message(text: str) -> dict[str, Any]:
    return {"role": "user", "content": text}
