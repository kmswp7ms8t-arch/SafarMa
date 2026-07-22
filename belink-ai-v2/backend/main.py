from __future__ import annotations

import argparse
import asyncio
import os
import time
from collections import defaultdict, deque
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent import BelinkChatAnswer, BelinkTravelDecision, TravelProfile, analyze_travel, chat_with_commander
from memory import MemoryStore, PrivatePreferences, TripFeedback

SERVICE_VERSION = "0.2.0"
DEFAULT_ORIGINS = "http://localhost:8080,http://127.0.0.1:8080"


def parse_origins() -> list[str]:
    values = [item.strip() for item in os.getenv("BELINK_CORS_ORIGINS", DEFAULT_ORIGINS).split(",")]
    return [value for value in values if value and value != "*"]


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
    mode: str
    answer: BelinkChatAnswer


app = FastAPI(title="Belink AI Travel Core", version=SERVICE_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Belink-Session"],
)

memory = MemoryStore()
limiter = SlidingWindowLimiter(
    limit=int(os.getenv("BELINK_RATE_LIMIT", "30")),
    window_seconds=int(os.getenv("BELINK_RATE_WINDOW_SECONDS", "60")),
)


def client_key(request: Request) -> str:
    session = request.headers.get("X-Belink-Session", "").strip()[:120]
    if session:
        return f"session:{session}"
    forwarded = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    host = forwarded or (request.client.host if request.client else "unknown")
    return f"ip:{host}"


async def rate_limit(request: Request) -> None:
    if not limiter.allow(client_key(request)):
        raise HTTPException(status_code=429, detail="Too many requests. Please retry shortly.")


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "Belink AI Travel Core",
        "version": SERVICE_VERSION,
        "ai_connected": bool(os.getenv("OPENAI_API_KEY")),
        "model": os.getenv("BELINK_AI_MODEL", "gpt-5-mini"),
    }


@app.get("/ready")
def ready() -> dict[str, Any]:
    database_ready = memory.ready()
    require_ai = os.getenv("BELINK_REQUIRE_AI", "false").casefold() == "true"
    ai_ready = bool(os.getenv("OPENAI_API_KEY"))
    is_ready = database_ready and (ai_ready or not require_ai)
    if not is_ready:
        raise HTTPException(status_code=503, detail="Belink AI is not ready")
    return {"status": "ready", "database": database_ready, "ai_connected": ai_ready, "offline_mode_available": True}


@app.post("/api/belink-ai/analyze", dependencies=[Depends(rate_limit)])
async def analyze(profile: TravelProfile) -> dict[str, Any]:
    try:
        decision, mode = await analyze_travel(profile)
        trip_id = memory.save_trip(profile, decision, mode)
        session_id = memory.save_session(profile, decision, [])
        return {"mode": mode, "trip_id": trip_id, "session_id": session_id, "decision": decision.model_dump()}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid travel profile") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Belink AI analysis could not be completed") from exc


@app.post("/api/belink-ai/chat", response_model=ChatResponse, dependencies=[Depends(rate_limit)])
async def chat(payload: ChatRequest) -> ChatResponse:
    stored = memory.get_session(payload.session_id) if payload.session_id else None
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
        raise HTTPException(status_code=502, detail="Belink Commander could not answer right now") from exc
    history.extend([
        {"role": "user", "content": payload.question[:1200]},
        {"role": "assistant", "content": answer.answer[:3000]},
    ])
    session_id = memory.save_session(profile, decision, history, payload.session_id)
    return ChatResponse(session_id=session_id, mode=mode, answer=answer)


@app.get("/api/belink-ai/memory", response_model=PrivatePreferences, dependencies=[Depends(rate_limit)])
def get_memory(user_id: str = "amir-sanaz") -> PrivatePreferences:
    return memory.get_preferences(user_id[:80])


@app.put("/api/belink-ai/memory", response_model=PrivatePreferences, dependencies=[Depends(rate_limit)])
def update_memory(preferences: PrivatePreferences) -> PrivatePreferences:
    return memory.put_preferences(preferences)


@app.delete("/api/belink-ai/memory", dependencies=[Depends(rate_limit)])
def delete_memory(user_id: str = "amir-sanaz") -> dict[str, bool]:
    memory.delete_preferences(user_id[:80])
    return {"deleted": True}


@app.get("/api/belink-ai/trips", dependencies=[Depends(rate_limit)])
def list_trips(user_id: str = "amir-sanaz", limit: int = 30) -> dict[str, Any]:
    return {"trips": memory.list_trips(user_id[:80], limit)}


@app.put("/api/belink-ai/trips/{trip_id}/feedback", dependencies=[Depends(rate_limit)])
def update_trip_feedback(trip_id: str, feedback: TripFeedback) -> dict[str, Any]:
    if not memory.set_trip_feedback(trip_id[:64], feedback.status):
        raise HTTPException(status_code=404, detail="Trip not found")
    return {"updated": True, "status": feedback.status}


@app.delete("/api/belink-ai/trips/{trip_id}", dependencies=[Depends(rate_limit)])
def delete_trip(trip_id: str) -> dict[str, bool]:
    if not memory.delete_trip(trip_id[:64]):
        raise HTTPException(status_code=404, detail="Trip not found")
    return {"deleted": True}


@app.delete("/api/belink-ai/chat/{session_id}", dependencies=[Depends(rate_limit)])
def delete_chat(session_id: str) -> dict[str, bool]:
    return {"deleted": memory.delete_session(session_id[:120])}


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
    if args.demo or not os.getenv("PORT"):
        asyncio.run(demo())
    else:
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
