from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agent import BelinkChatAnswer, BelinkTravelDecision, TravelProfile, analyze_travel, chat_with_commander
from auth import (
    CLIENT_HEADER,
    ClientIdentity,
    has_persistent_session_secret,
    issue_or_validate_client,
    require_client,
    validate_client_token,
)
from memory import MemoryStore, PrivatePreferences, TripFeedback

SERVICE_VERSION = "0.5.0"
DEFAULT_ORIGINS = "http://localhost:8080,http://127.0.0.1:8080"
logger = logging.getLogger("belink-ai")


def env_int(name: str, default: int, minimum: int = 0, maximum: int = 1_000_000) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(value, maximum))


def parse_origins() -> list[str]:
    values = [item.strip() for item in os.getenv("BELINK_CORS_ORIGINS", DEFAULT_ORIGINS).split(",")]
    result: list[str] = []
    for value in values:
        if not value or value == "*":
            continue
        try:
            parsed = urlparse(value)
        except ValueError:
            continue
        if parsed.scheme in {"http", "https"} and parsed.netloc and not parsed.path.strip("/"):
            result.append(f"{parsed.scheme}://{parsed.netloc}")
    return list(dict.fromkeys(result))


def utc_day_window() -> tuple[str, str, int]:
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    reset = start + timedelta(days=1)
    retry_after = max(1, int((reset - now).total_seconds()))
    return start.isoformat(), reset.isoformat(), retry_after


def profile_fingerprint(profile: TravelProfile) -> str:
    payload = json.dumps(profile.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def ai_connected() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def quota_settings() -> dict[str, int]:
    return {
        "analyses_per_day": env_int("BELINK_ANALYSES_PER_DAY", 5, 0, 10_000),
        "chats_per_day": env_int("BELINK_CHATS_PER_DAY", 50, 0, 100_000),
        "analysis_cache_seconds": env_int("BELINK_ANALYSIS_CACHE_SECONDS", 900, 0, 86_400),
    }


class SlidingWindowLimiter:
    def __init__(self, limit: int = 30, window_seconds: int = 60):
        self.limit = max(1, limit)
        self.window_seconds = max(1, window_seconds)
        self.events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        queue = self.events[key]
        cutoff = now - self.window_seconds
        while queue and queue[0] <= cutoff:
            queue.popleft()
        if len(queue) >= self.limit:
            return False
        queue.append(now)
        return True


class ChatRequest(BaseModel):
    session_id: str | None = Field(default=None, max_length=120)
    question: str = Field(min_length=1, max_length=1200)
    profile: TravelProfile | None = None
    latest_decision: BelinkTravelDecision | None = None


class ChatResponse(BaseModel):
    session_id: str
    client_token: str
    mode: str
    answer: BelinkChatAnswer
    usage: dict[str, Any]


app = FastAPI(
    title="Belink AI Travel Core",
    version=SERVICE_VERSION,
    docs_url="/docs" if os.getenv("BELINK_ENV", "development") != "production" else None,
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Belink-Session", CLIENT_HEADER],
    expose_headers=[CLIENT_HEADER],
    max_age=600,
)

memory = MemoryStore()
limiter = SlidingWindowLimiter(
    limit=env_int("BELINK_RATE_LIMIT", 30, 1, 100_000),
    window_seconds=env_int("BELINK_RATE_WINDOW_SECONDS", 60, 1, 86_400),
)


def usage_snapshot(user_id: str) -> dict[str, Any]:
    start, reset, _ = utc_day_window()
    counts = memory.usage_summary(user_id, start)
    settings = quota_settings()
    return {
        "window": "utc_day",
        "window_started_at": start,
        "resets_at": reset,
        "ai_connected": ai_connected(),
        "analyses": {
            "used": counts.get("analysis", 0),
            "limit": settings["analyses_per_day"],
            "cache_hits": counts.get("analysis_cache_hit", 0),
            "offline": counts.get("analysis_offline", 0),
        },
        "chats": {
            "used": counts.get("chat", 0),
            "limit": settings["chats_per_day"],
            "offline": counts.get("chat_offline", 0),
        },
        "analysis_cache_seconds": settings["analysis_cache_seconds"],
    }


def enforce_daily_quota(user_id: str, event_type: str, limit: int, label: str) -> None:
    if limit <= 0:
        return
    start, _, retry_after = utc_day_window()
    used = memory.count_usage_since(user_id, event_type, start)
    if used >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Daily Belink AI {label} limit reached ({limit} per UTC day).",
            headers={"Retry-After": str(retry_after)},
        )


@app.middleware("http")
async def security_and_size_headers(request: Request, call_next):
    max_body = env_int("BELINK_MAX_BODY_BYTES", 131_072, 16_384, 10_000_000)
    content_length = request.headers.get("content-length")
    if request.method in {"POST", "PUT", "PATCH"} and content_length:
        try:
            if int(content_length) > max_body:
                return JSONResponse(status_code=413, content={"detail": "Request body is too large"})
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length header"})
    response = await call_next(request)
    response.headers.setdefault("Cache-Control", "no-store")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    return response


def client_key(request: Request) -> str:
    identity = validate_client_token(request.headers.get(CLIENT_HEADER))
    if identity:
        return f"client:{identity.client_id}"
    forwarded = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    host = forwarded or (request.client.host if request.client else "unknown")
    return f"ip:{host}"


async def rate_limit(request: Request) -> None:
    if not limiter.allow(client_key(request)):
        raise HTTPException(status_code=429, detail="Too many requests. Please retry shortly.")


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "Belink AI Travel Core", "status": "ok", "version": SERVICE_VERSION}


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "Belink AI Travel Core",
        "version": SERVICE_VERSION,
        "ai_connected": ai_connected(),
        "model": os.getenv("BELINK_AI_MODEL", "gpt-5-mini"),
        "client_isolation": "signed",
        "persistent_session_secret": has_persistent_session_secret(),
        "data_export": True,
        "data_deletion": True,
        "commercial_guardrails": True,
        "quota": quota_settings(),
    }


@app.get("/ready")
def ready() -> dict[str, Any]:
    database_ready = memory.ready()
    require_ai = os.getenv("BELINK_REQUIRE_AI", "false").casefold() == "true"
    require_secret = (
        os.getenv("BELINK_ENV", "development").casefold() == "production"
        or os.getenv("BELINK_REQUIRE_SESSION_SECRET", "false").casefold() == "true"
    )
    ai_ready = ai_connected()
    secret_ready = has_persistent_session_secret()
    is_ready = database_ready and (ai_ready or not require_ai) and (secret_ready or not require_secret)
    if not is_ready:
        raise HTTPException(status_code=503, detail="Belink AI is not ready")
    return {
        "status": "ready",
        "database": database_ready,
        "ai_connected": ai_ready,
        "client_isolation": "signed",
        "persistent_session_secret": secret_ready,
        "offline_mode_available": True,
        "commercial_guardrails": True,
    }


@app.post("/api/belink-ai/analyze", dependencies=[Depends(rate_limit)])
async def analyze(
    profile: TravelProfile,
    identity: ClientIdentity = Depends(issue_or_validate_client),
) -> dict[str, Any]:
    settings = quota_settings()
    fingerprint = profile_fingerprint(profile)
    connected = ai_connected()
    cache_hit = False
    cached_at: str | None = None
    try:
        decision: BelinkTravelDecision
        mode: str
        cached = None
        if connected and settings["analysis_cache_seconds"] > 0:
            memory.purge_expired_cache(settings["analysis_cache_seconds"])
            cached = memory.get_cached_analysis(
                identity.client_id,
                fingerprint,
                settings["analysis_cache_seconds"],
            )
        if cached:
            decision = BelinkTravelDecision.model_validate(cached["decision"])
            mode = str(cached["mode"])
            cache_hit = True
            cached_at = str(cached["created_at"])
            memory.record_usage(identity.client_id, "analysis_cache_hit")
        else:
            if connected:
                enforce_daily_quota(
                    identity.client_id,
                    "analysis",
                    settings["analyses_per_day"],
                    "analysis",
                )
            decision, mode = await analyze_travel(profile)
            if mode == "connected":
                memory.record_usage(identity.client_id, "analysis")
                if settings["analysis_cache_seconds"] > 0:
                    memory.put_cached_analysis(identity.client_id, fingerprint, profile, decision, mode)
            else:
                memory.record_usage(identity.client_id, "analysis_offline")
        trip_id = memory.save_trip(profile, decision, mode, identity.client_id)
        session_id = memory.save_session(profile, decision, [], identity.client_id)
        return {
            "mode": mode,
            "cache_hit": cache_hit,
            "cached_at": cached_at,
            "trip_id": trip_id,
            "session_id": session_id,
            "client_token": identity.token,
            "decision": decision.model_dump(),
            "usage": usage_snapshot(identity.client_id),
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid travel profile") from exc
    except Exception as exc:
        logger.exception("Belink AI analysis failed")
        raise HTTPException(status_code=502, detail="Belink AI analysis could not be completed") from exc


@app.post("/api/belink-ai/chat", response_model=ChatResponse, dependencies=[Depends(rate_limit)])
async def chat(
    payload: ChatRequest,
    identity: ClientIdentity = Depends(issue_or_validate_client),
) -> ChatResponse:
    stored = memory.get_session(payload.session_id, identity.client_id) if payload.session_id else None
    profile_data = payload.profile.model_dump() if payload.profile else (stored or {}).get("profile")
    if not profile_data:
        raise HTTPException(status_code=422, detail="A travel profile is required for the first chat message")
    profile = TravelProfile.model_validate(profile_data)
    decision_data = payload.latest_decision.model_dump() if payload.latest_decision else (stored or {}).get("decision")
    decision = BelinkTravelDecision.model_validate(decision_data) if decision_data else None
    history = list((stored or {}).get("messages") or [])
    settings = quota_settings()
    if ai_connected():
        enforce_daily_quota(identity.client_id, "chat", settings["chats_per_day"], "chat")
    try:
        answer, mode = await chat_with_commander(profile, decision, payload.question, history)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Belink Commander chat failed")
        raise HTTPException(status_code=502, detail="Belink Commander could not answer right now") from exc
    memory.record_usage(identity.client_id, "chat" if mode == "connected" else "chat_offline")
    history.extend([
        {"role": "user", "content": payload.question[:1200]},
        {"role": "assistant", "content": answer.answer[:3000]},
    ])
    session_id = memory.save_session(profile, decision, history, identity.client_id, payload.session_id)
    return ChatResponse(
        session_id=session_id,
        client_token=identity.token,
        mode=mode,
        answer=answer,
        usage=usage_snapshot(identity.client_id),
    )


@app.get("/api/belink-ai/usage", dependencies=[Depends(rate_limit)])
def get_usage(identity: ClientIdentity = Depends(require_client)) -> dict[str, Any]:
    return usage_snapshot(identity.client_id)


@app.get("/api/belink-ai/memory", response_model=PrivatePreferences, dependencies=[Depends(rate_limit)])
def get_memory(identity: ClientIdentity = Depends(require_client)) -> PrivatePreferences:
    return memory.get_preferences(identity.client_id)


@app.put("/api/belink-ai/memory", response_model=PrivatePreferences, dependencies=[Depends(rate_limit)])
def update_memory(
    preferences: PrivatePreferences,
    identity: ClientIdentity = Depends(require_client),
) -> PrivatePreferences:
    return memory.put_preferences(preferences, identity.client_id)


@app.delete("/api/belink-ai/memory", dependencies=[Depends(rate_limit)])
def delete_memory(identity: ClientIdentity = Depends(require_client)) -> dict[str, bool]:
    memory.delete_preferences(identity.client_id)
    return {"deleted": True}


@app.get("/api/belink-ai/trips", dependencies=[Depends(rate_limit)])
def list_trips(limit: int = 30, identity: ClientIdentity = Depends(require_client)) -> dict[str, Any]:
    return {"trips": memory.list_trips(identity.client_id, limit)}


@app.put("/api/belink-ai/trips/{trip_id}/feedback", dependencies=[Depends(rate_limit)])
def update_trip_feedback(
    trip_id: str,
    feedback: TripFeedback,
    identity: ClientIdentity = Depends(require_client),
) -> dict[str, Any]:
    if not memory.set_trip_feedback(trip_id[:64], feedback.status, identity.client_id):
        raise HTTPException(status_code=404, detail="Trip not found")
    return {"updated": True, "status": feedback.status}


@app.delete("/api/belink-ai/trips/{trip_id}", dependencies=[Depends(rate_limit)])
def delete_trip(trip_id: str, identity: ClientIdentity = Depends(require_client)) -> dict[str, bool]:
    if not memory.delete_trip(trip_id[:64], identity.client_id):
        raise HTTPException(status_code=404, detail="Trip not found")
    return {"deleted": True}


@app.delete("/api/belink-ai/chat/{session_id}", dependencies=[Depends(rate_limit)])
def delete_chat(session_id: str, identity: ClientIdentity = Depends(require_client)) -> dict[str, bool]:
    return {"deleted": memory.delete_session(session_id[:120], identity.client_id)}


@app.get("/api/belink-ai/user-data", dependencies=[Depends(rate_limit)])
def export_user_data(identity: ClientIdentity = Depends(require_client)) -> dict[str, Any]:
    return memory.export_user_data(identity.client_id)


@app.delete("/api/belink-ai/user-data", dependencies=[Depends(rate_limit)])
def delete_all_user_data(identity: ClientIdentity = Depends(require_client)) -> dict[str, Any]:
    deleted = memory.delete_all_user_data(identity.client_id)
    return {"deleted": True, "records": deleted}


async def demo() -> None:
    profile = TravelProfile(
        origin="DOH",
        destination_candidates=["Trabzon", "Tbilisi", "Istanbul"],
        passport="Iran",
        residence_country="Qatar",
        departure_date="2026-08-06",
        return_date="2026-08-11",
        travelers=2,
        budget_qar=13_500,
        trip_style=["nature", "relaxation", "romantic"],
        language="fa",
    )
    decision, mode = await analyze_travel(profile)
    print(f"mode={mode}")
    print(decision.model_dump_json(indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if args.demo:
        asyncio.run(demo())
    else:
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8421")))
