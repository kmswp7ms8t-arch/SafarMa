from __future__ import annotations

import os
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

UsageKind = Literal["analyze", "chat"]


@dataclass(frozen=True)
class QuotaSnapshot:
    day: str
    analyze_used: int
    analyze_limit: int
    chat_used: int
    chat_limit: int
    global_used: int
    global_limit: int

    def model_dump(self) -> dict[str, int | str]:
        return {
            "day": self.day,
            "analyze_used": self.analyze_used,
            "analyze_limit": self.analyze_limit,
            "chat_used": self.chat_used,
            "chat_limit": self.chat_limit,
            "global_used": self.global_used,
            "global_limit": self.global_limit,
        }


class UsageLimitExceeded(RuntimeError):
    def __init__(self, message: str, snapshot: QuotaSnapshot):
        super().__init__(message)
        self.snapshot = snapshot


class UsageStore:
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
        return connection

    def _init_schema(self) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS ai_usage (
                    day TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    analyze_count INTEGER NOT NULL DEFAULT 0,
                    chat_count INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(day, user_id)
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_ai_usage_day ON ai_usage(day)"
            )

    @staticmethod
    def _day() -> str:
        return datetime.now(timezone.utc).date().isoformat()

    @staticmethod
    def limits() -> dict[str, int]:
        return {
            "analyze": max(1, int(os.getenv("BELINK_DAILY_ANALYSIS_LIMIT", "3"))),
            "chat": max(1, int(os.getenv("BELINK_DAILY_CHAT_LIMIT", "20"))),
            "global": max(1, int(os.getenv("BELINK_GLOBAL_DAILY_AI_LIMIT", "100"))),
        }

    def _snapshot(self, connection: sqlite3.Connection, user_id: str, day: str) -> QuotaSnapshot:
        row = connection.execute(
            "SELECT analyze_count, chat_count FROM ai_usage WHERE day = ? AND user_id = ?",
            (day, user_id),
        ).fetchone()
        global_row = connection.execute(
            "SELECT COALESCE(SUM(analyze_count + chat_count), 0) AS total FROM ai_usage WHERE day = ?",
            (day,),
        ).fetchone()
        limits = self.limits()
        return QuotaSnapshot(
            day=day,
            analyze_used=int(row["analyze_count"] if row else 0),
            analyze_limit=limits["analyze"],
            chat_used=int(row["chat_count"] if row else 0),
            chat_limit=limits["chat"],
            global_used=int(global_row["total"] if global_row else 0),
            global_limit=limits["global"],
        )

    def status(self, user_id: str) -> QuotaSnapshot:
        day = self._day()
        with self._connect() as connection:
            return self._snapshot(connection, user_id, day)

    def reserve(self, user_id: str, kind: UsageKind) -> QuotaSnapshot:
        day = self._day()
        column = "analyze_count" if kind == "analyze" else "chat_count"
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            before = self._snapshot(connection, user_id, day)
            used = before.analyze_used if kind == "analyze" else before.chat_used
            limit = before.analyze_limit if kind == "analyze" else before.chat_limit
            if used >= limit:
                connection.rollback()
                raise UsageLimitExceeded(f"Daily {kind} limit reached", before)
            if before.global_used >= before.global_limit:
                connection.rollback()
                raise UsageLimitExceeded("Global daily AI limit reached", before)
            now = datetime.now(timezone.utc).isoformat()
            connection.execute(
                f"""
                INSERT INTO ai_usage(day, user_id, {column}, updated_at)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(day, user_id) DO UPDATE SET
                    {column} = {column} + 1,
                    updated_at = excluded.updated_at
                """,
                (day, user_id, now),
            )
            connection.commit()
            return self._snapshot(connection, user_id, day)

    def refund(self, user_id: str, kind: UsageKind) -> None:
        day = self._day()
        column = "analyze_count" if kind == "analyze" else "chat_count"
        with self._lock, self._connect() as connection:
            connection.execute(
                f"""
                UPDATE ai_usage
                SET {column} = CASE WHEN {column} > 0 THEN {column} - 1 ELSE 0 END,
                    updated_at = ?
                WHERE day = ? AND user_id = ?
                """,
                (datetime.now(timezone.utc).isoformat(), day, user_id),
            )
