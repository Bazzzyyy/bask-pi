"""Record short WAV via sounddevice + scipy (optional) or arecord subprocess on Pi."""

from __future__ import annotations

import subprocess
import wave
from pathlib import Path


def record_wav_arecord(out_path: Path, seconds: float = 5.0, device: str = "", rate: int = 16000) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["arecord", "-f", "S16_LE", "-r", str(rate), "-c", "1", "-d", str(int(seconds))]
    if device:
        cmd.extend(["-D", device])
    cmd.append(str(out_path))
    subprocess.run(cmd, check=True)


def record_wav_sounddevice(out_path: Path, seconds: float = 5.0, rate: int = 16000) -> None:
    import numpy as np
    import sounddevice as sd

    frames = int(seconds * rate)
    audio = sd.rec(frames, samplerate=rate, channels=1, dtype="int16")
    sd.wait()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(audio.tobytes())


def record_wav(out_path: Path, seconds: float = 5.0, device: str = "", rate: int = 16000) -> None:
    try:
        record_wav_sounddevice(out_path, seconds=seconds, rate=rate)
    except Exception:
        record_wav_arecord(out_path, seconds=seconds, device=device, rate=rate)
