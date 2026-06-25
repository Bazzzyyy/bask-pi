"""Load YAML configuration for Bask."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class WebConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    admin_token: str = ""


@dataclass
class AudioConfig:
    output_device: str = ""
    input_device: str = ""
    sample_rate: int = 16000


@dataclass
class STTConfig:
    provider: str = "none"
    model: str = "whisper-1"


@dataclass
class TTSConfig:
    provider: str = "none"
    piper_binary: str = "piper"
    piper_voice: str = "en_US-lessac-medium"
    openai_voice: str = "alloy"


@dataclass
class OLEDGpio:
    spi_port: int = 0
    spi_device: int = 0
    dc_gpio: int = 24
    reset_gpio: int = 25
    backlight_gpio: int = 18


@dataclass
class OLEDConfig:
    enabled: bool = True
    backend: str = "auto"
    width: int = 240
    height: int = 240
    gpio: OLEDGpio = field(default_factory=OLEDGpio)


@dataclass
class LLMConfig:
    default_preset: str = "gpt_4o_mini"
    openai_base_url: str = "https://api.openai.com/v1"
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"


@dataclass
class CalendarConfig:
    credentials_path: str = "secrets/google_client_secret.json"
    token_path: str = "secrets/google_token.json"


@dataclass
class AppConfig:
    assistant_name: str = "Bask"
    web: WebConfig = field(default_factory=WebConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    stt: STTConfig = field(default_factory=STTConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    oled: OLEDConfig = field(default_factory=OLEDConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    calendar: CalendarConfig = field(default_factory=CalendarConfig)
    database_path: str = "data/bask.db"

    @classmethod
    def load(cls, path: Path) -> AppConfig:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls._from_dict(raw)

    @classmethod
    def _from_dict(cls, raw: dict[str, Any]) -> AppConfig:
        web = WebConfig(**raw.get("web", {}))
        audio = AudioConfig(**raw.get("audio", {}))
        stt = STTConfig(**raw.get("stt", {}))
        tts = TTSConfig(**raw.get("tts", {}))
        oled_raw = dict(raw.get("oled", {}) or {})
        gpio_raw = dict(oled_raw.pop("gpio", {}) or {})
        oled = OLEDConfig(**oled_raw, gpio=OLEDGpio(**gpio_raw))
        llm = LLMConfig(**raw.get("llm", {}))
        cal = CalendarConfig(**raw.get("calendar", {}))
        return cls(
            assistant_name=raw.get("assistant_name", "Bask"),
            web=web,
            audio=audio,
            stt=stt,
            tts=tts,
            oled=oled,
            llm=llm,
            calendar=cal,
            database_path=raw.get("database_path", "data/bask.db"),
        )

    def resolve_path(self, base: Path, rel: str) -> Path:
        p = Path(rel)
        return p if p.is_absolute() else (base / p).resolve()
