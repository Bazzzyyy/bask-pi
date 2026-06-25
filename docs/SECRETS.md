# Secrets (do not commit real keys)

## profiles.json

Create `secrets/profiles.json`:

```json
{
  "profiles": [
    {
      "id": "default",
      "label": "Personal",
      "openai_api_key": "",
      "deepseek_api_key": "",
      "dashscope_api_key": ""
    }
  ],
  "active_profile_id": "default",
  "active_model_preset": "gpt_4o_mini"
}
```

Model presets: `deepseek_v3`, `qwen_vl`, `gpt_4o_mini`, `gpt_5_nano`

## Google Calendar

Place OAuth **Desktop** client JSON from Google Cloud Console at `secrets/google_client_secret.json`.
After first OAuth run, `secrets/google_token.json` will be created.
