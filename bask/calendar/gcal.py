"""Google Calendar API helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def get_credentials(client_secret_path: Path, token_path: Path) -> Credentials:
    creds: Credentials | None = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not client_secret_path.exists():
                raise FileNotFoundError(
                    f"Missing {client_secret_path} — add OAuth Desktop client JSON from Google Cloud."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def calendar_service(client_secret_path: Path, token_path: Path):
    creds = get_credentials(client_secret_path, token_path)
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def list_today_events(service, calendar_id: str = "primary", max_results: int = 10) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=1)
    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=now.isoformat(),
            timeMax=end.isoformat(),
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return events_result.get("items", [])


def create_event(
    service,
    summary: str,
    start: datetime,
    end: datetime | None = None,
    calendar_id: str = "primary",
) -> dict[str, Any]:
    end = end or (start + timedelta(hours=1))
    body = {
        "summary": summary,
        "start": {"dateTime": start.isoformat()},
        "end": {"dateTime": end.isoformat()},
    }
    return service.events().insert(calendarId=calendar_id, body=body).execute()
