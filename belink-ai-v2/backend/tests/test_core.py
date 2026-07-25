import importlib
import os
import sqlite3

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from agent import (
    BelinkTravelDecision,
    CostBreakdown,
    SourceEvidence,
    SpecialistFinding,
    TravelProfile,
    deterministic_fallback,
    enforce_decision_policy,
)
from auth import issue_client_token, validate_client_token
from memory import MemoryStore


def source(title, url, classification="official"):
    return SourceEvidence(title=title, url=url, classification=classification, supported_claims=[title])


def finding(name, status="good", verification="verified", sources=None):
    return SpecialistFinding(specialist=name, status=status, verification_status=verification, summary=name, sources=sources or [])


def decision(findings, verdict="feasible"):
    return BelinkTravelDecision(
        verdict=verdict,
        confidence=91,
        primary_destination="Trabzon",
        why_this_destination="Fit",
        executive_summary="Summary",
        cost=CostBreakdown(flights=4000, accommodation=2500, food=1200, local_transport=900, activities=600, contingency=800, total_low=9000, total_high=11000),
        specialist_findings=findings,
        next_actions=["Verify"],
        answer_to_user="Answer",
    )


def verified_findings():
    return [
        finding("Belink Pilot", sources=[source("Airline timetable", "https://www.qatarairways.com/")]),
        finding("Belink Visa Officer", sources=[source("Official entry rules", "https://www.mfa.gov.tr/")]),
        finding("Belink Safety Analyst", sources=[source("Official advisory", "https://www.gov.uk/foreign-travel-advice/turkey")]),
        finding("Belink Budget Controller", verification="estimated"),
        finding("Belink Tour Leader", verification="estimated"),
    ]


def profile(language="fa", budget=13500):
    return TravelProfile(origin="DOH", destination_candidates=["Trabzon", "Tbilisi"], passport="Iran", departure_date="2026-08-06", return_date="2026-08-11", travelers=2, budget_qar=budget, language=language)


def build_client(tmp_path, monkeypatch):
    monkeypatch.setenv("BELINK_AI_DATABASE", str(tmp_path / "api.sqlite3"))
    monkeypatch.setenv("BELINK_SESSION_SECRET", "test-secret-that-is-stable-and-private")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("BELINK_ENV", raising=False)
    import main
    importlib.reload(main)
    return TestClient(main.app)


def test_feasible_requires_critical_sources():
    result = enforce_decision_policy(decision([finding("Belink Budget Controller")]))
    assert result.verdict == "needs_verification"
    assert result.confidence <= 68


def test_verified_result_can_remain_feasible():
    assert enforce_decision_policy(decision(verified_findings())).verdict == "feasible"


def test_unsafe_destination_is_blocked():
    rows = verified_findings()
    rows[2] = finding("Belink Safety Analyst", status="blocked", sources=[source("Official advisory", "https://www.gov.uk/foreign-travel-advice/turkey")])
    assert enforce_decision_policy(decision(rows, "conditional")).verdict == "not_feasible"


def test_invalid_source_url_is_rejected():
    with pytest.raises(ValidationError):
        source("Fake", "javascript:alert(1)")


def test_offline_mode_is_never_falsely_feasible():
    result = deterministic_fallback(profile())
    assert result.verdict != "feasible"
    assert result.confidence < 70
    assert "آفلاین" in result.answer_to_user


def test_over_budget_offline_result_is_not_feasible():
    assert deterministic_fallback(profile(language="en", budget=1000)).verdict == "not_feasible"


def test_signed_client_token_round_trip(monkeypatch):
    monkeypatch.setenv("BELINK_SESSION_SECRET", "unit-test-secret")
    issued = issue_client_token()
    validated = validate_client_token(issued.token)
    assert validated is not None
    assert validated.client_id == issued.client_id
    assert validate_client_token(issued.token + "tampered") is None


def test_health_ready_analyze_and_chat(tmp_path, monkeypatch):
    client = build_client(tmp_path, monkeypatch)
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200
    analyzed_response = client.post("/api/belink-ai/analyze", json=profile().model_dump())
    assert analyzed_response.status_code == 200
    analyzed = analyzed_response.json()
    assert analyzed["mode"] == "offline"
    assert validate_client_token(analyzed["client_token"]) is not None
    headers = {"X-Belink-Client": analyzed["client_token"]}
    answer = client.post(
        "/api/belink-ai/chat",
        headers=headers,
        json={"session_id": analyzed["session_id"], "question": "ویزا و پاسپورت چطور؟"},
    )
    assert answer.status_code == 200
    assert answer.json()["session_id"] == analyzed["session_id"]
    assert answer.json()["client_token"] == analyzed["client_token"]


def test_private_endpoints_require_valid_client(tmp_path, monkeypatch):
    client = build_client(tmp_path, monkeypatch)
    assert client.get("/api/belink-ai/memory").status_code == 401
    assert client.get("/api/belink-ai/trips").status_code == 401
    assert client.get("/api/belink-ai/trips", headers={"X-Belink-Client": "invalid"}).status_code == 401


def test_client_trip_isolation(tmp_path, monkeypatch):
    client = build_client(tmp_path, monkeypatch)
    first = client.post("/api/belink-ai/analyze", json=profile().model_dump()).json()
    second = client.post("/api/belink-ai/analyze", json=profile(language="en").model_dump()).json()
    first_headers = {"X-Belink-Client": first["client_token"]}
    second_headers = {"X-Belink-Client": second["client_token"]}
    first_trips = client.get("/api/belink-ai/trips", headers=first_headers).json()["trips"]
    second_trips = client.get("/api/belink-ai/trips", headers=second_headers).json()["trips"]
    assert len(first_trips) == 1
    assert len(second_trips) == 1
    assert first_trips[0]["id"] != second_trips[0]["id"]
    assert client.delete(f"/api/belink-ai/trips/{first_trips[0]['id']}", headers=second_headers).status_code == 404


def test_cross_client_cannot_take_over_conversation(tmp_path, monkeypatch):
    client = build_client(tmp_path, monkeypatch)
    first = client.post("/api/belink-ai/analyze", json=profile().model_dump()).json()
    second = client.post("/api/belink-ai/analyze", json=profile(language="en").model_dump()).json()
    first_headers = {"X-Belink-Client": first["client_token"]}
    second_headers = {"X-Belink-Client": second["client_token"]}

    attempted_takeover = client.post(
        "/api/belink-ai/chat",
        headers=second_headers,
        json={
            "session_id": first["session_id"],
            "profile": profile(language="en").model_dump(),
            "question": "Can I use this session?",
        },
    )
    assert attempted_takeover.status_code == 200
    assert attempted_takeover.json()["session_id"] != first["session_id"]

    original_owner = client.post(
        "/api/belink-ai/chat",
        headers=first_headers,
        json={"session_id": first["session_id"], "question": "هنوز همان جلسه است؟"},
    )
    assert original_owner.status_code == 200
    assert original_owner.json()["session_id"] == first["session_id"]


def test_rc2_conversation_schema_migrates_before_index_creation(tmp_path):
    database = tmp_path / "rc2.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.executescript("""
            CREATE TABLE conversations (
                session_id TEXT PRIMARY KEY,
                profile_json TEXT NOT NULL,
                decision_json TEXT,
                messages_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            INSERT INTO conversations(session_id, profile_json, decision_json, messages_json, updated_at)
            VALUES ('legacy-session', '{}', NULL, '[]', '2026-07-22T00:00:00Z');
        """)

    store = MemoryStore(str(database))
    assert store.ready()
    with sqlite3.connect(database) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(conversations)")}
        indexes = {row[1] for row in connection.execute("PRAGMA index_list(conversations)")}
        owner = connection.execute(
            "SELECT user_id FROM conversations WHERE session_id = 'legacy-session'"
        ).fetchone()[0]
    assert "user_id" in columns
    assert "idx_conversations_user_updated" in indexes
    assert owner == "legacy"


def test_production_readiness_requires_persistent_secret(tmp_path, monkeypatch):
    monkeypatch.setenv("BELINK_AI_DATABASE", str(tmp_path / "ready.sqlite3"))
    monkeypatch.setenv("BELINK_ENV", "production")
    monkeypatch.delenv("BELINK_SESSION_SECRET", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("BELINK_REQUIRE_AI", "false")
    import main
    importlib.reload(main)
    client = TestClient(main.app)
    assert client.get("/ready").status_code == 503
    monkeypatch.setenv("BELINK_SESSION_SECRET", "production-test-secret")
    importlib.reload(main)
    client = TestClient(main.app)
    assert client.get("/ready").status_code == 200
