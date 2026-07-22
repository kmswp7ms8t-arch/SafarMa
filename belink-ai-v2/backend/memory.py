from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from agent import BelinkTravelDecision, TravelProfile


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PrivatePreferences(BaseModel):
    user_id: str = Field(default="amir-sanaz", min_length=2, max_length=80)
    preferred_styles: list[str] = Field(default_factory=list, max_length=20)
    rejected_destinations: list[str] = Field(default_factory=list, max_length=50)
    accepted_destinations: list[str] = Field(default_factory=list, max_length=50)
    budget_preference_qar: float | None = Field(default=None, gt=0, le=2_000_000)
    accommodation_preference: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=2000)


class TripFeedback(BaseModel):
    status: str = Field(pattern="^(accepted|rejected|saved)$")


class MemoryStore:
    def __init__(self, path: str | None = None):
        configured = path or os.getenv("BELINK_AI_DATABASE", "./data/belink_ai.sqlite3")
        self.path = Path(configured)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _init_schema(self) -> None:
        with self._lock, self._connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS preferences (
                    user_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS trips (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    profile_json TEXT NOT NULL,
                    decision_json TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    feedback TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS conversations (
                    session_id TEXT PRIMARY KEY,
                    profile_json TEXT NOT NULL,
                    decision_json TEXT,
                    messages_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

    def ready(self) -> bool:
        try:
            with self._connect() as connection:
                connection.execute("SELECT 1").fetchone()
            return True
        except sqlite3.Error:
            return False

    def get_preferences(self, user_id: str = "amir-sanaz") -> PrivatePreferences:
        with self._connect() as connection:
            row = connection.execute("SELECT payload FROM preferences WHERE user_id = ?", (user_id,)).fetchone()
        return PrivatePreferences(user_id=user_id) if not row else PrivatePreferences.model_validate_json(row["payload"])

    def put_preferences(self, preferences: PrivatePreferences) -> PrivatePreferences:
        with self._lock, self._connect() as connection:
            connection.execute(
                """INSERT INTO preferences(user_id, payload, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at""",
                (preferences.user_id, preferences.model_dump_json(), utc_now()),
            )
        return preferences

    def delete_preferences(self, user_id: str = "amir-sanaz") -> None:
        with self._lock, self._connect() as connection:
            connection.execute("DELETE FROM preferences WHERE user_id = ?", (user_id,))

    def save_trip(self, profile: TravelProfile, decision: BelinkTravelDecision, mode: str, user_id: str = "amir-sanaz") -> str:
        trip_id = uuid.uuid4().hex
        with self._lock, self._connect() as connection:
            connection.execute(
                """INSERT INTO trips(id, user_id, profile_json, decision_json, mode, feedback, created_at)
                VALUES (?, ?, ?, ?, ?, NULL, ?)""",
                (trip_id, user_id, profile.model_dump_json(), decision.model_dump_json(), mode, utc_now()),
            )
        return trip_id

    def list_trips(self, user_id: str = "amir-sanaz", limit: int = 30) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 100))
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM trips WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, safe_limit)).fetchall()
        return [{"id": row["id"], "profile": json.loads(row["profile_json"]), "decision": json.loads(row["decision_json"]), "mode": row["mode"], "feedback": row["feedback"], "created_at": row["created_at"]} for row in rows]

    def set_trip_feedback(self, trip_id: str, status: str) -> bool:
        with self._lock, self._connect() as connection:
            cursor = connection.execute("UPDATE trips SET feedback = ? WHERE id = ?", (status, trip_id))
        return cursor.rowcount > 0

    def delete_trip(self, trip_id: str) -> bool:
        with self._lock, self._connect() as connection:
            cursor = connection.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
        return cursor.rowcount > 0

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM conversations WHERE session_id = ?", (session_id,)).fetchone()
        if not row:
            return None
        return {"session_id": row["session_id"], "profile": json.loads(row["profile_json"]), "decision": json.loads(row["decision_json"]) if row["decision_json"] else None, "messages": json.loads(row["messages_json"]), "updated_at": row["updated_at"]}

    def save_session(self, profile: TravelProfile, decision: BelinkTravelDecision | None, messages: list[dict[str, str]], session_id: str | None = None) -> str:
        identifier = session_id or uuid.uuid4().hex
        with self._lock, self._connect() as connection:
            connection.execute(
                """INSERT INTO conversations(session_id, profile_json, decision_json, messages_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET profile_json=excluded.profile_json, decision_json=excluded.decision_json, messages_json=excluded.messages_json, updated_at=excluded.updated_at""",
                (identifier, profile.model_dump_json(), decision.model_dump_json() if decision else None, json.dumps(messages[-20:], ensure_ascii=False), utc_now()),
            )
        return identifier

    def delete_session(self, session_id: str) -> bool:
        with self._lock, self._connect() as connection:
            cursor = connection.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
        return cursor.rowcount > 0
