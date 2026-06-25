"""Route chat + optional image to the right provider and model."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from bask.config import AppConfig, LLMConfig
from bask.llm import clients
from bask.secrets_store import Profile

# Model IDs — verify against provider docs when deploying.
PRESETS: dict[str, dict[str, Any]] = {
    "deepseek_v3": {"provider": "deepseek", "model": "deepseek-chat", "vision": False},
    "qwen_vl": {"provider": "dashscope", "model": "qwen-vl-plus", "vision": True},
    "gpt_4o_mini": {"provider": "openai", "model": "gpt-4o-mini", "vision": True},
    "gpt_5_nano": {"provider": "openai", "model": "gpt-5-nano", "vision": True},
}


def _system_message(system_prompt: str) -> dict[str, Any]:
    return {"role": "system", "content": system_prompt}


async def complete_chat(
    *,
    cfg: AppConfig,
    profile: Profile,
    llm: LLMConfig,
    preset_id: str,
    user_text: str,
    system_prompt: str,
    image_bytes: bytes | None = None,
) -> str:
    preset = PRESETS.get(preset_id) or PRESETS["gpt_4o_mini"]
    want_vision = image_bytes is not None

    # Fallback: vision request but preset is text-only → use OpenAI mini if key present
    if want_vision and not preset.get("vision"):
        if profile.openai_api_key:
            preset = PRESETS["gpt_4o_mini"]
        elif profile.dashscope_api_key:
            preset = PRESETS["qwen_vl"]
        else:
            raise RuntimeError("Vision requested but no OpenAI or DashScope key in profile")

    provider = preset["provider"]
    model = preset["model"]
    messages: list[dict[str, Any]] = [_system_message(system_prompt)]

    if want_vision:
        messages.append(clients.build_vision_user_message(user_text, image_bytes))
    else:
        messages.append(clients.build_text_user_message(user_text))

    if provider == "openai":
        if not profile.openai_api_key:
            raise RuntimeError("OpenAI API key missing for this preset")
        return await clients.chat_completion(
            base_url=llm.openai_base_url,
            api_key=profile.openai_api_key,
            model=model,
            messages=messages,
        )

    if provider == "deepseek":
        if not profile.deepseek_api_key:
            raise RuntimeError("DeepSeek API key missing for this preset")
        if want_vision:
            raise RuntimeError("DeepSeek preset used with image — use qwen_vl or gpt_4o_mini")
        return await clients.chat_completion(
            base_url=llm.deepseek_base_url,
            api_key=profile.deepseek_api_key,
            model=model,
            messages=messages,
        )

    if provider == "dashscope":
        if not profile.dashscope_api_key:
            raise RuntimeError("DashScope API key missing for Qwen-VL")
        return await clients.chat_completion(
            base_url=llm.dashscope_base_url,
            api_key=profile.dashscope_api_key,
            model=model,
            messages=messages,
        )

    raise RuntimeError(f"Unknown provider {provider}")


def load_system_prompt(package_dir: Path) -> str:
    p = package_dir / "llm" / "prompts" / "bask_system.txt"
    if p.exists():
        return p.read_text(encoding="utf-8").strip()
    return "You are Bask, a helpful assistant."
