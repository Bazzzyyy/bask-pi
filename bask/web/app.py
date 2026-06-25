"""Local FastAPI settings UI: profiles and model preset."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from bask.config import AppConfig
from bask.secrets_store import load_profiles, save_profiles


def build_app(cfg: AppConfig, profiles_path: Path, project_root: Path) -> FastAPI:
    app = FastAPI(title="Bask Settings", docs_url=None, redoc_url=None)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "name": "Bask"}

    def admin_token() -> str:
        return os.environ.get("BASK_ADMIN_TOKEN", cfg.web.admin_token or "")

    async def require_admin(authorization: str | None = Header(default=None)) -> None:
        tok = admin_token()
        if not tok:
            raise HTTPException(503, "Admin token not configured")
        if authorization != f"Bearer {tok}":
            raise HTTPException(401, "Unauthorized")

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return """<!doctype html><html><head><meta charset=utf-8><title>Bask</title></head>
        <body><h1>Bask</h1><p>Use <code>/api/profiles</code> with Bearer admin token.</p></body></html>"""

    @app.get("/api/profiles")
    async def get_profiles(_: None = Depends(require_admin)) -> dict:
        st = load_profiles(profiles_path)
        return {
            "active_profile_id": st.active_profile_id,
            "active_model_preset": st.active_model_preset,
            "profiles": [{"id": p.id, "label": p.label} for p in st.profiles],
        }

    class ProfileKeys(BaseModel):
        openai_api_key: str | None = None
        deepseek_api_key: str | None = None
        dashscope_api_key: str | None = None

    class ActiveBody(BaseModel):
        active_profile_id: str
        active_model_preset: str | None = None

    @app.post("/api/profiles/active")
    async def set_active(body: ActiveBody, _: None = Depends(require_admin)) -> dict:
        st = load_profiles(profiles_path)
        st.active_profile_id = body.active_profile_id
        if body.active_model_preset:
            st.active_model_preset = body.active_model_preset
        save_profiles(profiles_path, st)
        return {"ok": True}

    @app.put("/api/profiles/{profile_id}/keys")
    async def put_keys(profile_id: str, body: ProfileKeys, _: None = Depends(require_admin)) -> dict:
        st = load_profiles(profiles_path)
        found = False
        for p in st.profiles:
            if p.id == profile_id:
                if body.openai_api_key is not None:
                    p.openai_api_key = body.openai_api_key
                if body.deepseek_api_key is not None:
                    p.deepseek_api_key = body.deepseek_api_key
                if body.dashscope_api_key is not None:
                    p.dashscope_api_key = body.dashscope_api_key
                found = True
                break
        if not found:
            raise HTTPException(404, "profile not found")
        save_profiles(profiles_path, st)
        return {"ok": True}

    return app
