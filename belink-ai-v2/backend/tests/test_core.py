import importlib
import os

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


def test_health_ready_analyze_and_chat(tmp_path):
    os.environ["BELINK_AI_DATABASE"] = str(tmp_path / "api.sqlite3")
    os.environ.pop("OPENAI_API_KEY", None)
    import main
    importlib.reload(main)
    client = TestClient(main.app)
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200
    analyzed = client.post("/api/belink-ai/analyze", json=profile().model_dump()).json()
    assert analyzed["mode"] == "offline"
    answer = client.post("/api/belink-ai/chat", json={"session_id": analyzed["session_id"], "question": "ویزا و پاسپورت چطور؟"})
    assert answer.status_code == 200
    assert answer.json()["session_id"] == analyzed["session_id"]
