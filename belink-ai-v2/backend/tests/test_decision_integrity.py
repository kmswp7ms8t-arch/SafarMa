from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent import (
    BelinkTravelDecision,
    CostBreakdown,
    SourceEvidence,
    SpecialistFinding,
    TravelProfile,
    enforce_decision_policy,
)


def profile(**overrides):
    values = {
        "origin": "DOH",
        "destination_candidates": ["Trabzon"],
        "passport": "Iran",
        "departure_date": "2026-08-06",
        "return_date": "2026-08-11",
        "travelers": 2,
        "budget_qar": 13500,
    }
    values.update(overrides)
    return TravelProfile(**values)


def evidence(title, url, classification="official", verification_status="verified"):
    return SourceEvidence(
        title=title,
        url=url,
        classification=classification,
        verification_status=verification_status,
        supported_claims=[title],
    )


def finding(name, sources=None, verification_status="verified"):
    return SpecialistFinding(
        specialist=name,
        status="good",
        summary=f"{name} summary",
        verification_status=verification_status,
        sources=sources or [],
    )


def feasible_decision(entry_source=None, safety_source=None, route_source=None):
    return BelinkTravelDecision(
        verdict="feasible",
        confidence=94,
        primary_destination="Trabzon",
        why_this_destination="Strong initial fit.",
        executive_summary="The trip appears feasible after verification.",
        cost=CostBreakdown(
            flights=4000,
            accommodation=2500,
            food=1200,
            local_transport=900,
            activities=600,
            contingency=800,
            total_low=9000,
            total_high=11000,
        ),
        specialist_findings=[
            finding("Belink Pilot", [route_source or evidence("Current route", "https://www.qatarairways.com/", "commercial")]),
            finding("Belink Visa Officer", [entry_source or evidence("Official entry rule", "https://www.mfa.gov.tr/")]),
            finding("Belink Safety Analyst", [safety_source or evidence("Official safety advice", "https://www.gov.uk/foreign-travel-advice/turkey")]),
            finding("Belink Budget Controller", verification_status="estimated"),
        ],
        next_actions=["Recheck before payment"],
        answer_to_user="The trip appears feasible after verification.",
    )


def test_return_must_be_after_departure():
    with pytest.raises(ValidationError):
        profile(return_date="2026-08-06")
    with pytest.raises(ValidationError):
        profile(return_date="2026-08-05")


def test_trip_cannot_exceed_one_year():
    with pytest.raises(ValidationError):
        profile(return_date="2027-08-10")


def test_cost_high_cannot_be_below_low_or_component_subtotal():
    with pytest.raises(ValidationError):
        CostBreakdown(
            flights=1000,
            accommodation=1000,
            food=500,
            local_transport=200,
            activities=100,
            contingency=200,
            total_low=4000,
            total_high=3000,
        )
    with pytest.raises(ValidationError):
        CostBreakdown(
            flights=1000,
            accommodation=1000,
            food=500,
            local_transport=200,
            activities=100,
            contingency=200,
            total_low=1000,
            total_high=2000,
        )


def test_source_requires_a_supported_claim():
    with pytest.raises(ValidationError):
        SourceEvidence(
            title="Official page",
            url="https://example.gov/entry",
            classification="official",
            supported_claims=[],
        )


def test_estimated_official_source_cannot_support_feasible_verdict():
    result = enforce_decision_policy(
        feasible_decision(
            entry_source=evidence(
                "Official entry rule",
                "https://www.mfa.gov.tr/",
                verification_status="estimated",
            )
        )
    )
    assert result.verdict == "needs_verification"
    assert any("entry" in item for item in result.unknowns)


def test_policy_sets_a_current_server_timestamp():
    old = "2020-01-01T00:00:00+00:00"
    candidate = feasible_decision()
    candidate.checked_at = old
    result = enforce_decision_policy(candidate)
    checked = datetime.fromisoformat(result.checked_at)
    assert checked.tzinfo is not None
    assert checked > datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_claim_backed_verified_evidence_can_remain_feasible():
    result = enforce_decision_policy(feasible_decision())
    assert result.verdict == "feasible"
    assert result.confidence == 94
