# Bask Pi Assistant

Voice + camera + OLED assistant for Raspberry Pi 3B+, orchestrating cloud LLMs (DeepSeek V3, Qwen-VL, GPT-4o mini, GPT-5 Nano), reminders, Google Calendar, and TTS via the 3.5 mm jack.

## Quick start (development)

```bash
cd bask-pi
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy config.example.yaml config.yaml
# Set secrets\profiles.json (see docs/SECRETS.md)
python -m bask.main --config config.yaml
```

On Raspberry Pi: install `picamera2` and display drivers per your OLED module; see `docs/HARDWARE_CHECKLIST.md`.

## Configuration

- `config.yaml` — non-secret settings (see `config.example.yaml`).
- `secrets/profiles.json` — API keys per profile (chmod 600 on Pi).
- Environment: `BASK_ADMIN_TOKEN` for the local settings web UI.

## systemd

Copy `systemd/bask.service` to `/etc/systemd/system/`, edit paths and `User=`, then `systemctl enable --now bask`.
