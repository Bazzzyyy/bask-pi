"""SQLite reminder storage."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass
class Reminder:
    id: int
    title: str
    fire_at: datetime
    repeat: str | None


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            fire_at TEXT NOT NULL,
            repeat TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def add_reminder(conn: sqlite3.Connection, title: str, fire_at: datetime, repeat: str | None = None) -> int:
    now = datetime.utcnow().isoformat()
    cur = conn.execute(
        "INSERT INTO reminders (title, fire_at, repeat, created_at) VALUES (?, ?, ?, ?)",
        (title, fire_at.isoformat(), repeat, now),
    )
    conn.commit()
    return int(cur.lastrowid)


def due_reminders(conn: sqlite3.Connection, now: datetime | None = None) -> list[Reminder]:
    now = now or datetime.utcnow()
    cur = conn.execute(
        "SELECT id, title, fire_at, repeat FROM reminders WHERE fire_at <= ? ORDER BY fire_at",
        (now.isoformat(),),
    )
    rows = cur.fetchall()
    return [
        Reminder(id=r["id"], title=r["title"], fire_at=datetime.fromisoformat(r["fire_at"]), repeat=r["repeat"])
        for r in rows
    ]


def delete_reminder(conn: sqlite3.Connection, rid: int) -> None:
    conn.execute("DELETE FROM reminders WHERE id = ?", (rid,))
    conn.commit()


def list_upcoming(conn: sqlite3.Connection, limit: int = 20) -> list[Reminder]:
    cur = conn.execute(
        "SELECT id, title, fire_at, repeat FROM reminders ORDER BY fire_at LIMIT ?",
        (limit,),
    )
    return [
        Reminder(id=r["id"], title=r["title"], fire_at=datetime.fromisoformat(r["fire_at"]), repeat=r["repeat"])
        for r in cur.fetchall()
    ]
