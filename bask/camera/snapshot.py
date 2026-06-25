"""Capture still frames from Raspberry Pi camera (picamera2)."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Tuple


def capture_jpeg(max_width: int = 1024, quality: int = 82) -> Tuple[bytes, str]:
    """
    Returns (jpeg_bytes, mime_type).
    Raises RuntimeError if camera unavailable.
    """
    try:
        from picamera2 import Picamera2  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "picamera2 not installed — run on Raspberry Pi OS with camera enabled."
        ) from e

    picam2 = Picamera2()
    cfg = picam2.create_still_configuration(
        main={"size": (max_width, max_width)}, buffer_count=2
    )
    picam2.configure(cfg)
    picam2.start()
    try:
        arr = picam2.capture_array("main")
        from PIL import Image

        img = Image.fromarray(arr).convert("RGB")
        w, h = img.size
        if max(w, h) > max_width:
            ratio = max_width / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        raw = buf.getvalue()
        if not raw:
            raise RuntimeError("Empty JPEG from camera")
        return raw, "image/jpeg"
    finally:
        picam2.stop()
        picam2.close()


def save_test_frame(path: Path, max_width: int = 640) -> None:
    jpeg, _ = capture_jpeg(max_width=max_width)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(jpeg)
