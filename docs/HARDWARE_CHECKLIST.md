# Bask — hardware verification (Raspberry Pi 3B+)

Use this checklist on the Pi before relying on full stack features.

## OS

- [ ] Raspberry Pi OS **64-bit** Bookworm (recommended for `picamera2`).
- [ ] `uname -m` shows `aarch64`.

## Interfaces

- [ ] **SPI** enabled (`raspi-config` → Interface Options → SPI), reboot if needed.
- [ ] **I2C** enabled if your OLED uses I2C instead of SPI.
- [ ] **Camera** enabled; `libcamera-hello` or `rpicam-hello` runs (CSI module).

## OLED (SPI colour typical)

- [ ] Wiring matches your module datasheet (MOSI, SCLK, CE/CS, DC, RST, 3.3V, GND).
- [ ] Note GPIO numbers in `config.yaml` under `oled.gpio`.

## Audio

- [ ] **Microphone**: USB mic detected (`arecord -l`) or ReSpeaker HAT per your setup.
- [ ] **Output**: plug earphones into **3.5 mm jack**; `speaker-test -t wav -c 2` or `aplay` on a short WAV succeeds.
- [ ] Set `audio_output_device` in `config.yaml` if default sink is wrong (`aplay -L` / `wpctl status` on PipeWire).

## Network

- [ ] Stable Wi-Fi or Ethernet for cloud LLM / STT / TTS APIs.

## Optional later (post-MVP)

- [ ] Servo power separate from Pi 3.3V; PWM GPIO for pan/tilt when you add `vision/`.
