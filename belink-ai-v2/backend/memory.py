from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from agent import BelinkTravelDecision, TravelProfile


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


class PrivatePreferences(BaseModel):
    user_id: str = Field(min_length=2, max_length=80)
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

    @staticmethod
    def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
        return {row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}

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
                    user_id TEXT NOT NULL,
                    profile_json TEXT NOT NULL,
                    decision_json TEXT,
                    messages_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS usage_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS analysis_cache (
                    user_id TEXT NOT NULL,
                    profile_hash TEXT NOT NULL,
                    profile_json TEXT NOT NULL,
                    decision_json TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, profile_hash)
                );
            """)
            if "user_id" not in self._columns(connection, "conversations"):
                connection.execute(
                    "ALTER TABLE conversations ADD COLUMN user_id TEXT NOT NULL DEFAULT 'legacy'"
                )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_trips_user_created ON trips(user_id, created_at DESC)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_conversations_user_updated ON conversations(user_id, updated_at DESC)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_usage_user_type_created ON usage_events(user_id, event_type, created_at DESC)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_cache_created ON analysis_cache(created_at)"
            )

    def ready(self) -> bool:
        try:
            with self._connect() as connection:
                connection.execute("SELECT 1").fetchone()
            return True
        except sqlite3.Error:
            return False

    def get_preferences(self, user_id: str) -> PrivatePreferences:
        with self._connect() as connection:
            row = connection.execute("SELECT payload FROM preferences WHERE user_id = ?", (user_id,)).fetchone()
        return PrivatePreferences(user_id=user_id) if not row else PrivatePreferences.model_validate_json(row["payload"])

    def put_preferences(self, preferences: PrivatePreferences, user_id: str) -> PrivatePreferences:
        scoped = preferences.model_copy(update={"user_id": user_id})
        with self._lock, self._connect() as connection:
            connection.execute(
                """INSERT INTO preferences(user_id, payload, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at""",
                (user_id, scoped.model_dump_json(), utc_now()),
            )
        return scoped

    def delete_preferences(self, user_id: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("DELETE FROM preferences WHERE user_id = ?", (user_id,))

    def save_trip(self, profile: TravelProfile, decision: BelinkTravelDecision, mode: str, user_id: str) -> str:
        trip_id = uuid.uuid4().hex
        with self._lock, self._connect() as connection:
            connection.execute(
                """INSERT INTO trips(id, user_id, profile_json, decision_json, mode, feedback, created_at)
                VALUES (?, ?, ?, ?, ?, NULL, ?)""",
                (trip_id, user_id, profile.model_dump_json(), decision.model_dump_json(), mode, utc_now()),
            )
        return trip_id

    def list_trips(self, user_id: str, limit: int = 30) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 1000))
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM trips WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, safe_limit),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "profile": json.loads(row["profile_json"]),
                "decision": json.loads(row["decision_json"]),
                "mode": row["mode"],
                "feedback": row["feedback"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def list_sessions(self, user_id: str, limit: int = 1000) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 1000))
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
                (user_id, safe_limit),
            ).fetchall()
        return [
            {
                "session_id": row["session_id"],
                "profile": json.loads(row["profile_json"]),
                "decision": json.loads(row["decision_json"]) if row["decision_json"] else None,
                "messages": json.loads(row["messages_json"]),
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def record_usage(self, user_id: str, event_type: str) -> None:
        clean_type = event_type.strip().casefold()[:64]
        if not clean_type:
            raise ValueError("event_type is required")
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT INTO usage_events(user_id, event_type, created_at) VALUES (?, ?, ?)",
                (user_id, clean_type, utc_now()),
            )

    def count_usage_since(self, user_id: str, event_type: str, since: str) -> int:
        with self._connect() as connection:
            row = connection.execute(
                """SELECT COUNT(*) AS total FROM usage_events
                WHERE user_id = ? AND event_type = ? AND created_at >= ?""",
                (user_id, event_type.strip().casefold()[:64], since),
            ).fetchone()
        return int(row["total"] if row else 0)

    def usage_summary(self, user_id: str, since: str) -> dict[str, int]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT event_type, COUNT(*) AS total FROM usage_events
                WHERE user_id = ? AND created_at >= ?
                GROUP BY event_type""",
                (user_id, since),
            ).fetchall()
        return {row["event_type"]: int(row["total"]) for row in rows}

    def list_usage_events(self, user_id: str, limit: int = 1000) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 5000))
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT event_type, created_at FROM usage_events
                WHERE user_id = ? ORDER BY created_at DESC LIMIT ?""",
                (user_id, safe_limit),
            ).fetchall()
        return [{"event_type": row["event_type"], "created_at": row["created_at"]} for row in rows]

    def get_cached_analysis(
        self,
        user_id: str,
        profile_hash: str,
        max_age_seconds: int,
    ) -> dict[str, Any] | None:
        if max_age_seconds <= 0:
            return None
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=max_age_seconds)
        with self._connect() as connection:
            row = connection.execute(
                """SELECT profile_json, decision_json, mode, created_at
                FROM analysis_cache WHERE user_id = ? AND profile_hash = ?""",
                (user_id, profile_hash),
            ).fetchone()
        if not row:
            return None
        try:
            created_at = parse_utc(row["created_at"])
        except (TypeError, ValueError):
            return None
        if created_at < cutoff:
            return None
        return {
            "profile": json.loads(row["profile_json"]),
            "decision": json.loads(row["decision_json"]),
            "mode": row["mode"],
            "created_at": row["created_at"],
        }

    def put_cached_analysis(
        self,
        user_id: str,
        profile_hash: str,
        profile: TravelProfile,
        decision: BelinkTravelDecision,
        mode: str,
    ) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """INSERT INTO analysis_cache(user_id, profile_hash, profile_json, decision_json, mode, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, profile_hash) DO UPDATE SET
                    profile_json=excluded.profile_json,
                    decision_json=excluded.decision_json,
                    mode=excluded.mode,
                    created_at=excluded.created_at""",
                (
                    user_id,
                    profile_hash,
                    profile.model_dump_json(),
                    decision.model_dump_json(),
                    mode,
                    utc_now(),
                ),
            )

    def list_cached_analyses(self, user_id: str, limit: int = 1000) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 1000))
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT profile_hash, profile_json, decision_json, mode, created_at
                FROM analysis_cache WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?""",
                (user_id, safe_limit),
            ).fetchall()
        return [
            {
                "profile_hash": row["profile_hash"],
                "profile": json.loads(row["profile_json"]),
                "decision": json.loads(row["decision_json"]),
                "mode": row["mode"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def purge_expired_cache(self, max_age_seconds: int) -> int:
        if max_age_seconds <= 0:
            return 0
        cutoff = (datetime.now(timezone.utc) - timedelta(seconds=max_age_seconds)).isoformat()
        with self._lock, self._connect() as connection:
            deleted = connection.execute(
                "DELETE FROM analysis_cache WHERE created_at < ?",
                (cutoff,),
            ).rowcount
        return max(0, deleted)

    def export_user_data(self, user_id: str) -> dict[str, Any]:
        return {
            "format": "safarma-user-data-v2",
            "exported_at": utc_now(),
            "anonymous_client_id": user_id,
            "preferences": self.get_preferences(user_id).model_dump(),
            "trips": self.list_trips(user_id, 1000),
            "conversations": self.list_sessions(user_id, 1000),
            "usage_events": self.list_usage_events(user_id, 5000),
            "cached_analyses": self.list_cached_analyses(user_id, 1000),
        }

    def set_trip_feedback(self, trip_id: str, status: str, user_id: str) -> bool:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                "UPDATE trips SET feedback = ? WHERE id = ? AND user_id = ?",
                (status, trip_id, user_id),
            )
        return cursor.rowcount > 0

    def delete_trip(self, trip_id: str, user_id: str) -> bool:
        with self._lock, self._connect() as connection:
            cursor = connection.execute("DELETE FROM trips WHERE id = ? AND user_id = ?", (trip_id, user_id))
        return cursor.rowcount > 0

    def get_session(self, session_id: str, user_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM conversations WHERE session_id = ? AND user_id = ?",
                (session_id, user_id),
            ).fetchone()
        if not row:
            return None
        return {
            "session_id": row["session_id"],
            "profile": json.loads(row["profile_json"]),
            "decision": json.loads(row["decision_json"]) if row["decision_json"] else None,
            "messages": json.loads(row["messages_json"]),
            "updated_at": row["updated_at"],
        }

    def save_session(
        self,
        profile: TravelProfile,
        decision: BelinkTravelDecision | None,
        messages: list[dict[str, str]],
        user_id: str,
        session_id: str | None = None,
    ) -> str:
        identifier = session_id or uuid.uuid4().hex
        with self._lock, self._connect() as connection:
            if session_id:
                owner = connection.execute(
                    "SELECT user_id FROM conversations WHERE session_id = ?",
                    (session_id,),
                ).fetchone()
                if owner and owner["user_id"] != user_id:
                    identifier = uuid.uuid4().hex
            connection.execute(
                """INSERT INTO conversations(session_id, user_id, profile_json, decision_json, messages_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET profile_json=excluded.profile_json,
                decision_json=excluded.decision_json, messages_json=excluded.messages_json,
                updated_at=excluded.updated_at
                WHERE conversations.user_id = excluded.user_id""",
                (
                    identifier,
                    user_id,
                    profile.model_dump_json(),
                    decision.model_dump_json() if decision else None,
                    json.dumps(messages[-20:], ensure_ascii=False),
                    utc_now(),
                ),
            )
        return identifier

    def delete_session(self, session_id: str, user_id: str) -> bool:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM conversations WHERE session_id = ? AND user_id = ?",
                (session_id, user_id),
            )
        return cursor.rowcount > 0

    def delete_all_user_data(self, user_id: str) -> dict[str, int]:
        with self._lock, self._connect() as connection:
            preferences = connection.execute("DELETE FROM preferences WHERE user_id = ?", (user_id,)).rowcount
            trips = connection.execute("DELETE FROM trips WHERE user_id = ?", (user_id,)).rowcount
            conversations = connection.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,)).rowcount
            usage_events = connection.execute("DELETE FROM usage_events WHERE user_id = ?", (user_id,)).rowcount
            cached_analyses = connection.execute("DELETE FROM analysis_cache WHERE user_id = ?", (user_id,)).rowcount
        return {
            "preferences": max(0, preferences),
            "trips": max(0, trips),
            "conversations": max(0, conversations),
            "usage_events": max(0, usage_events),
            "cached_analyses": max(0, cached_analyses),
        }
