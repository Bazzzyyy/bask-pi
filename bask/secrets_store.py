"""Load and save API profiles (OpenAI, DeepSeek, DashScope)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class Profile:
    id: str
    label: str
    openai_api_key: str = ""
    deepseek_api_key: str = ""
    dashscope_api_key: str = ""


@dataclass
class ProfilesState:
    profiles: list[Profile]
    active_profile_id: str
    active_model_preset: str

    @classmethod
    def default_state(cls) -> ProfilesState:
        return cls(
            profiles=[Profile(id="default", label="Default")],
            active_profile_id="default",
            active_model_preset="gpt_4o_mini",
        )

    def active_profile(self) -> Profile:
        for p in self.profiles:
            if p.id == self.active_profile_id:
                return p
        return self.profiles[0]


def load_profiles(path: Path) -> ProfilesState:
    if not path.exists():
        st = ProfilesState.default_state()
        path.parent.mkdir(parents=True, exist_ok=True)
        save_profiles(path, st)
        return st
    data = json.loads(path.read_text(encoding="utf-8"))
    profiles = [Profile(**p) for p in data.get("profiles", [])]
    if not profiles:
        profiles = [Profile(id="default", label="Default")]
    return ProfilesState(
        profiles=profiles,
        active_profile_id=data.get("active_profile_id", profiles[0].id),
        active_model_preset=data.get("active_model_preset", "gpt_4o_mini"),
    )


def save_profiles(path: Path, state: ProfilesState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "profiles": [asdict(p) for p in state.profiles],
        "active_profile_id": state.active_profile_id,
        "active_model_preset": state.active_model_preset,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
