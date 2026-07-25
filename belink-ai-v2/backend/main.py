from __future__ import annotations

import argparse
import asyncio
import logging
import os
import time
from collections import defaultdict, deque
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

SERVICE_VERSION = "0.3.0"
DEFAULT_ORIGINS = "http://localhost:8080,http://127.0.0.1:8080"
logger = logging.getLogger("belink-ai")


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
    limit=int(os.getenv("BELINK_RATE_LIMIT", "30")),
    window_seconds=int(os.getenv("BELINK_RATE_WINDOW_SECONDS", "60")),
)


@app.middleware("http")
async def security_and_size_headers(request: Request, call_next):
    max_body = max(16_384, int(os.getenv("BELINK_MAX_BODY_BYTES", "131072")))
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
        "ai_connected": bool(os.getenv("OPENAI_API_KEY")),
        "model": os.getenv("BELINK_AI_MODEL", "gpt-5-mini"),
        "client_isolation": "signed",
        "persistent_session_secret": has_persistent_session_secret(),
    }


@app.get("/ready")
def ready() -> dict[str, Any]:
    database_ready = memory.ready()
    require_ai = os.getenv("BELINK_REQUIRE_AI", "false").casefold() == "true"
    require_secret = (
        os.getenv("BELINK_ENV", "development").casefold() == "production"
        or os.getenv("BELINK_REQUIRE_SESSION_SECRET", "false").casefold() == "true"
    )
    ai_ready = bool(os.getenv("OPENAI_API_KEY"))
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
    }


@app.post("/api/belink-ai/analyze", dependencies=[Depends(rate_limit)])
async def analyze(
    profile: TravelProfile,
    identity: ClientIdentity = Depends(issue_or_validate_client),
) -> dict[str, Any]:
    try:
        decision, mode = await analyze_travel(profile)
        trip_id = memory.save_trip(profile, decision, mode, identity.client_id)
        session_id = memory.save_session(profile, decision, [], identity.client_id)
        return {
            "mode": mode,
            "trip_id": trip_id,
            "session_id": session_id,
            "client_token": identity.token,
            "decision": decision.model_dump(),
        }
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
    try:
        answer, mode = await chat_with_commander(profile, decision, payload.question, history)
    except Exception as exc:
        logger.exception("Belink Commander chat failed")
        raise HTTPException(status_code=502, detail="Belink Commander could not answer right now") from exc
    history.extend([
        {"role": "user", "content": payload.question[:1200]},
        {"role": "assistant", "content": answer.answer[:3000]},
    ])
    session_id = memory.save_session(profile, decision, history, identity.client_id, payload.session_id)
    return ChatResponse(session_id=session_id, client_token=identity.token, mode=mode, answer=answer)


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


@app.delete("/api/belink-ai/user-data", dependencies=[Depends(rate_limit)])
def delete_all_user_data(identity: ClientIdentity = Depends(require_client)) -> dict[str, bool]:
    memory.delete_all_user_data(identity.client_id)
    return {"deleted": True}


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
