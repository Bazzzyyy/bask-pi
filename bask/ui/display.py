"""OLED / LCD display abstraction: mock for dev, luma for SPI on Pi."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw, ImageFont

if TYPE_CHECKING:
    pass


class UIState(str, Enum):
    idle = "idle"
    listening = "listening"
    thinking = "thinking"
    speaking = "speaking"


class DisplayBackend(ABC):
    @abstractmethod
    def show_state(self, state: UIState, line1: str = "", line2: str = "") -> None:
        ...


class MockDisplay(DisplayBackend):
    """Logs and optionally saves PNG previews."""

    def __init__(self, width: int = 240, height: int = 240, dump_dir: Path | None = None) -> None:
        self.width = width
        self.height = height
        self.dump_dir = dump_dir

    def _render(self, state: UIState, line1: str, line2: str) -> Image.Image:
        img = Image.new("RGB", (self.width, self.height), color=(20, 24, 32))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()
        draw.text((8, 8), f"Bask — {state.value}", fill=(120, 200, 255), font=font)
        y = 36
        for line in (line1, line2):
            if line:
                draw.text((8, y), line[:40], fill=(230, 230, 230), font=font)
                y += 16
        return img

    def show_state(self, state: UIState, line1: str = "", line2: str = "") -> None:
        img = self._render(state, line1, line2)
        if self.dump_dir:
            self.dump_dir.mkdir(parents=True, exist_ok=True)
            path = self.dump_dir / f"ui_{state.value}.png"
            img.save(path)


def create_display(
    *,
    backend: str,
    width: int,
    height: int,
    gpio: object | None = None,
    dump_dir: Path | None = None,
) -> DisplayBackend:
    b = (backend or "auto").lower()
    if b == "mock":
        return MockDisplay(width, height, dump_dir=dump_dir)

    if b in ("auto", "luma"):
        try:
            from luma.core.interface.serial import spi  # type: ignore
            from luma.lcd.device import st7789  # type: ignore

            serial = spi(
                port=0,
                device=0,
                gpio_DC=getattr(gpio, "dc_gpio", 24),
                gpio_RST=getattr(gpio, "reset_gpio", 25),
            )
            device = st7789(serial, width=width, height=height, rotate=0)

            class LumaDisplay(DisplayBackend):
                def show_state(self, state: UIState, line1: str = "", line2: str = "") -> None:
                    img = Image.new(device.mode, device.size)
                    dr = ImageDraw.Draw(img)
                    dr.text((4, 4), f"Bask {state.value}", fill="cyan")
                    y = 24
                    for t in (line1, line2):
                        if t:
                            dr.text((4, y), t[:32], fill="white")
                            y += 14
                    device.display(img.convert(device.mode))

            return LumaDisplay()
        except Exception:
            if b == "luma":
                raise
            return MockDisplay(width, height, dump_dir=dump_dir)

    return MockDisplay(width, height, dump_dir=dump_dir)
