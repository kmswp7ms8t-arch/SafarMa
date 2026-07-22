from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timezone
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

try:
    from agents import Agent, Runner, WebSearchTool, function_tool
except ImportError:
    Agent = Runner = WebSearchTool = None
    def function_tool(func=None, **_kwargs):
        return func if func is not None else (lambda wrapped: wrapped)

VerificationStatus = Literal["verified", "estimated", "unknown", "conflicting"]
FindingStatus = Literal["good", "conditional", "blocked", "unknown"]
Verdict = Literal["feasible", "conditional", "not_feasible", "needs_verification"]
SourceClass = Literal["official", "community", "commercial", "reference"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_valid_public_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc) and not parsed.username and not parsed.password


class TravelProfile(BaseModel):
    origin: str = Field(min_length=2, max_length=120)
    destination_candidates: list[str] = Field(default_factory=list, max_length=8)
    passport: str = Field(min_length=2, max_length=80)
    passport_expiry: str | None = None
    residence_country: str | None = Field(default=None, max_length=80)
    residence_status: str | None = Field(default=None, max_length=40)
    residence_expiry: str | None = None
    departure_date: str
    return_date: str
    travelers: int = Field(default=2, ge=1, le=12)
    budget_qar: float = Field(gt=0, le=2_000_000)
    trip_style: list[str] = Field(default_factory=list, max_length=8)
    flight_preference: Literal["direct", "prefer_direct", "one_stop", "any"] = "prefer_direct"
    accommodation: str = Field(default="4-star hotel", max_length=80)
    transport_preference: str = Field(default="only if needed", max_length=80)
    food_preference: str = Field(default="balanced", max_length=80)
    halal_required: bool = True
    language: Literal["fa", "en"] = "fa"
    user_question: str | None = Field(default=None, max_length=1200)

    @field_validator("destination_candidates", "trip_style")
    @classmethod
    def clean_string_lists(cls, values: list[str]) -> list[str]:
        clean: list[str] = []
        for item in values:
            text = re.sub(r"\s+", " ", str(item)).strip()[:120]
            if text and text.casefold() not in {row.casefold() for row in clean}:
                clean.append(text)
        return clean

    @field_validator("departure_date", "return_date", "passport_expiry", "residence_expiry")
    @classmethod
    def validate_iso_dates(cls, value: str | None) -> str | None:
        if not value:
            return value
        date.fromisoformat(value)
        return value


class SourceEvidence(BaseModel):
    title: str = Field(min_length=2, max_length=240)
    url: str = Field(min_length=8, max_length=2000)
    source_type: str = Field(default="web", max_length=80)
    classification: SourceClass = "reference"
    checked_at: str = Field(default_factory=utc_now)
    supported_claims: list[str] = Field(default_factory=list, max_length=10)
    verification_status: VerificationStatus = "verified"

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if not is_valid_public_url(value):
            raise ValueError("Source URL must be a public HTTP(S) URL")
        return value


class SpecialistFinding(BaseModel):
    specialist: str
    status: FindingStatus
    summary: str
    verification_status: VerificationStatus = "unknown"
    evidence_needed: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    sources: list[SourceEvidence] = Field(default_factory=list, max_length=12)


class CostBreakdown(BaseModel):
    flights: float = Field(ge=0)
    accommodation: float = Field(ge=0)
    food: float = Field(ge=0)
    local_transport: float = Field(ge=0)
    activities: float = Field(ge=0)
    contingency: float = Field(ge=0)
    total_low: float = Field(ge=0)
    total_high: float = Field(ge=0)


class BelinkTravelDecision(BaseModel):
    brand: str = "Belink AI"
    commander: str = "Belink Commander"
    verdict: Verdict
    confidence: int = Field(ge=0, le=100)
    primary_destination: str
    why_this_destination: str
    alternatives: list[str] = Field(default_factory=list, max_length=3)
    executive_summary: str
    decision_rationale: list[str] = Field(default_factory=list, max_length=10)
    cost: CostBreakdown
    specialist_findings: list[SpecialistFinding]
    sources: list[SourceEvidence] = Field(default_factory=list, max_length=30)
    assumptions: list[str] = Field(default_factory=list, max_length=20)
    unknowns: list[str] = Field(default_factory=list, max_length=20)
    next_actions: list[str]
    answer_to_user: str
    checked_at: str = Field(default_factory=utc_now)


class BelinkChatAnswer(BaseModel):
    answer: str
    verification_status: VerificationStatus = "unknown"
    sources: list[SourceEvidence] = Field(default_factory=list, max_length=12)
    assumptions: list[str] = Field(default_factory=list, max_length=10)
    unknowns: list[str] = Field(default_factory=list, max_length=10)
    suggested_questions: list[str] = Field(default_factory=list, max_length=4)


@function_tool
def budget_stress_test(budget_qar: float, flights: float, accommodation: float, food: float, local_transport: float, activities: float, contingency_rate: float = 0.10) -> dict[str, float | str]:
    """Calculate a transparent travel budget range and budget pressure."""
    subtotal = sum(max(0, value) for value in (flights, accommodation, food, local_transport, activities))
    contingency = subtotal * max(0.05, min(contingency_rate, 0.25))
    high = subtotal + contingency
    low = subtotal * 0.93
    ratio = high / max(budget_qar, 1)
    pressure = "comfortable" if ratio <= 0.95 else "tight" if ratio <= 1.08 else "over_budget"
    return {"flights": round(flights, 2), "accommodation": round(accommodation, 2), "food": round(food, 2), "local_transport": round(local_transport, 2), "activities": round(activities, 2), "contingency": round(contingency, 2), "total_low": round(low, 2), "total_high": round(high, 2), "budget_pressure": pressure, "budget_gap": round(budget_qar - high, 2)}


@function_tool
def date_sanity_check(departure_date: str, return_date: str) -> dict[str, Any]:
    """Validate travel dates and calculate trip length."""
    try:
        start = date.fromisoformat(departure_date)
        end = date.fromisoformat(return_date)
    except ValueError:
        return {"valid": False, "reason": "Dates must use YYYY-MM-DD"}
    days = (end - start).days + 1
    return {"valid": days >= 2, "days": days, "reason": "ok" if days >= 2 else "Return must be after departure"}


MODEL = os.getenv("BELINK_AI_MODEL", "gpt-5-mini")
COMMON_RULES = """
You are part of Belink AI, a private travel intelligence system for Amir and Sanaz.
Be direct, practical, premium and evidence-aware. Never invent live prices, route availability,
visa rules, passport-validity rules, safety facts, ratings, reviews or URLs. Use web search when
current facts matter. Prefer official immigration, foreign-ministry, embassy, airline, airport,
IATA and official advisory sources. Community sources may support traveller sentiment only.
Every source-backed claim must include a valid public URL and supported_claims. Mark estimates,
unknowns and conflicts explicitly. Visa eligibility is not approval. Do not assume a universal
six-month passport-validity rule. Return only the requested structured output.
"""


def _research_tools() -> list[Any]:
    if WebSearchTool is None:
        return []
    return [WebSearchTool(search_context_size="high", external_web_access=True)]


def build_agents() -> tuple[Any, Any]:
    if Agent is None or Runner is None:
        raise RuntimeError("openai-agents is not installed")
    pilot = Agent(name="Belink Pilot", model=MODEL, output_type=SpecialistFinding, tools=_research_tools(), instructions=COMMON_RULES + "Assess routes, schedules, transit implications and aviation practicality. Verify route claims with current evidence.")
    visa = Agent(name="Belink Visa Officer", model=MODEL, output_type=SpecialistFinding, tools=_research_tools(), instructions=COMMON_RULES + "Assess tourist visa, entry, passport validity, residence-based rules and transit visas using official sources.")
    safety = Agent(name="Belink Safety Analyst", model=MODEL, output_type=SpecialistFinding, tools=_research_tools(), instructions=COMMON_RULES + "Assess official advisories, regional risk and operational disruption. Community reports are supplementary only.")
    budget = Agent(name="Belink Budget Controller", model=MODEL, output_type=SpecialistFinding, tools=[budget_stress_test, date_sanity_check, *_research_tools()], instructions=COMMON_RULES + "Stress-test the whole trip in QAR. Use live evidence when available and otherwise state ranges and assumptions.")
    tour = Agent(name="Belink Tour Leader", model=MODEL, output_type=SpecialistFinding, tools=_research_tools(), instructions=COMMON_RULES + "Assess pace, areas to stay, car need, halal access, food, activities, seasonality and traveller sentiment.")
    commander = Agent(name="Belink Commander", model=MODEL, output_type=BelinkTravelDecision, tools=[pilot.as_tool("belink_pilot", "Analyze route and aviation practicality with current evidence."), visa.as_tool("belink_visa_officer", "Analyze visa, passport, residence and transit rules."), safety.as_tool("belink_safety_analyst", "Analyze official safety and operational risks."), budget.as_tool("belink_budget_controller", "Stress-test the full trip budget."), tour.as_tool("belink_tour_leader", "Analyze itinerary, food, activities and traveller fit."), budget_stress_test, date_sanity_check], instructions=COMMON_RULES + "You own the final answer. Consult all five specialists. A feasible verdict requires sufficiently verified entry/passport, safety and route checks plus a realistic budget.")
    chat = Agent(name="Belink Commander Chat", model=MODEL, output_type=BelinkChatAnswer, tools=_research_tools(), instructions=COMMON_RULES + "Answer follow-up questions using the supplied profile and latest decision. Preserve context and never claim unresearched live data.")
    return commander, chat


def _dedupe_sources(findings: list[SpecialistFinding], top_sources: list[SourceEvidence]) -> list[SourceEvidence]:
    result: list[SourceEvidence] = []
    seen: set[str] = set()
    for source in [*top_sources, *(source for finding in findings for source in finding.sources)]:
        key = source.url.rstrip("/").casefold()
        if key not in seen:
            seen.add(key)
            result.append(source)
    return result[:30]


def enforce_decision_policy(decision: BelinkTravelDecision) -> BelinkTravelDecision:
    decision.sources = _dedupe_sources(decision.specialist_findings, decision.sources)
    critical_names = {"belink pilot": "route", "belink visa officer": "entry", "belink safety analyst": "safety", "belink budget controller": "budget"}
    critical: dict[str, SpecialistFinding] = {}
    for finding in decision.specialist_findings:
        name = finding.specialist.casefold().strip()
        for expected, key in critical_names.items():
            if expected in name:
                critical[key] = finding
                break
    blockers = [finding for finding in critical.values() if finding.status == "blocked"]
    missing = [key for key in critical_names.values() if key not in critical]
    unverified = [key for key, finding in critical.items() if finding.verification_status not in {"verified", "estimated"}]
    entry, safety, route = critical.get("entry"), critical.get("safety"), critical.get("route")
    official_entry = bool(entry and any(source.classification == "official" for source in entry.sources))
    official_safety = bool(safety and any(source.classification == "official" for source in safety.sources))
    route_evidence = bool(route and route.sources)
    if blockers:
        decision.verdict = "not_feasible"
        decision.confidence = min(decision.confidence, 90)
    elif decision.verdict == "feasible" and (missing or unverified or not official_entry or not official_safety or not route_evidence):
        decision.verdict = "needs_verification"
        decision.confidence = min(decision.confidence, 68)
        gaps = [*missing, *unverified]
        if not official_entry: gaps.append("official entry source")
        if not official_safety: gaps.append("official safety source")
        if not route_evidence: gaps.append("route evidence")
        decision.unknowns = list(dict.fromkeys([*decision.unknowns, *gaps]))[:20]
    return decision


def deterministic_fallback(profile: TravelProfile) -> BelinkTravelDecision:
    destination = profile.destination_candidates[0] if profile.destination_candidates else "Worldwide shortlist"
    trip_days = max(2, (date.fromisoformat(profile.return_date) - date.fromisoformat(profile.departure_date)).days + 1)
    base = max(2800.0, profile.budget_qar * 0.78)
    flights, accommodation, food, transport, activities = base * 0.38, base * 0.23, base * 0.14, base * 0.10, base * 0.08
    subtotal = flights + accommodation + food + transport + activities
    contingency = subtotal * 0.10
    high, low = subtotal + contingency, subtotal * 0.93
    verdict: Verdict = "needs_verification" if high <= profile.budget_qar else "conditional" if low <= profile.budget_qar * 1.08 else "not_feasible"
    fa = profile.language == "fa"
    summary = f"این نتیجه آفلاین و تأییدنشده است. {destination} برای سفر {trip_days} روزه از نظر بودجه اولیه قابل بررسی است، اما ویزا، اعتبار پاسپورت، امنیت، مسیر و موجودی زنده هنوز باید تأیید شوند." if fa else f"This is an offline, unverified result. {destination} is worth checking for a {trip_days}-day trip, but visa, passport validity, safety, route and live availability still require verification."
    finding = SpecialistFinding(specialist="Belink AI Offline Core", status="unknown", verification_status="unknown", summary=summary, evidence_needed=["live route evidence", "official entry rules", "official safety advisory", "live lodging evidence"], unknowns=["entry rules", "passport validity", "safety advisory", "live route and prices"], actions=["Connect the server-side OpenAI runtime and run connected analysis"])
    return BelinkTravelDecision(verdict=verdict, confidence=48, primary_destination=destination, why_this_destination="براساس گزینه‌های واردشده و تناسب اولیه با بودجه و مدت سفر؛ نه براساس داده زنده." if fa else "Based on entered options and initial budget/duration fit, not live data.", alternatives=profile.destination_candidates[1:4], executive_summary=summary, decision_rationale=["Offline deterministic estimate", "Critical checks remain unverified"], cost=CostBreakdown(flights=round(flights), accommodation=round(accommodation), food=round(food), local_transport=round(transport), activities=round(activities), contingency=round(contingency), total_low=round(low), total_high=round(high)), specialist_findings=[finding], assumptions=["Costs are proportional estimates derived from the supplied total budget"], unknowns=finding.unknowns, next_actions=["Verify official entry and passport rules", "Check official safety advice", "Check current flights and accommodation", "Run connected Belink AI analysis"], answer_to_user=summary)


def offline_chat(profile: TravelProfile, decision: BelinkTravelDecision | None, question: str) -> BelinkChatAnswer:
    fa = profile.language == "fa"
    current = decision or deterministic_fallback(profile)
    text = question.casefold()
    if any(token in text for token in ("budget", "cost", "هزینه", "بودجه")):
        answer = f"برآورد فعلی {current.cost.total_low:,.0f} تا {current.cost.total_high:,.0f} ریال قطر است؛ این عدد تخمینی است و قیمت زنده محسوب نمی‌شود." if fa else f"The current estimate is QAR {current.cost.total_low:,.0f}–{current.cost.total_high:,.0f}; it is an estimate, not a live quote."
    elif any(token in text for token in ("visa", "passport", "ویزا", "پاسپورت")):
        answer = "قانون ویزا و اعتبار پاسپورت هنوز از منبع رسمی تأیید نشده است؛ تا قبل از بررسی رسمی، نتیجه مشروط می‌ماند." if fa else "Visa and passport-validity rules are not yet verified from an official source, so the decision remains conditional."
    elif any(token in text for token in ("alternative", "cheaper", "جایگزین", "ارزان")):
        alternatives = "، ".join(current.alternatives) if current.alternatives else ("هنوز مشخص نشده" if fa else "not available yet")
        answer = f"گزینه‌های فعلی: {alternatives}. برای مقایسه دقیق‌تر باید قیمت و شرایط ورود زنده بررسی شود." if fa else f"Current alternatives: {alternatives}. Live prices and entry rules are needed for a precise comparison."
    else:
        answer = current.answer_to_user
    return BelinkChatAnswer(answer=answer, verification_status="unknown", unknowns=current.unknowns, suggested_questions=["ریسک اصلی چیست؟", "گزینه ارزان‌تر چیست؟", "مدارک ورود چیست؟"] if fa else ["What is the main risk?", "What is cheaper?", "Which entry documents are needed?"])


async def analyze_travel(profile: TravelProfile) -> tuple[BelinkTravelDecision, str]:
    if not os.getenv("OPENAI_API_KEY"):
        return deterministic_fallback(profile), "offline"
    commander, _ = build_agents()
    prompt = "Analyze this travel profile as Belink AI. Consult every specialist, use web research for current facts, and return an evidence-aware structured recommendation.\n\n" + profile.model_dump_json(indent=2)
    result = await Runner.run(commander, prompt, max_turns=20)
    return enforce_decision_policy(BelinkTravelDecision.model_validate(result.final_output)), "connected"


async def chat_with_commander(profile: TravelProfile, decision: BelinkTravelDecision | None, question: str, history: list[dict[str, str]] | None = None) -> tuple[BelinkChatAnswer, str]:
    if not os.getenv("OPENAI_API_KEY"):
        return offline_chat(profile, decision, question), "offline"
    _, chat = build_agents()
    payload = {"profile": profile.model_dump(), "latest_decision": decision.model_dump() if decision else None, "recent_messages": (history or [])[-8:], "question": question}
    result = await Runner.run(chat, json.dumps(payload, ensure_ascii=False), max_turns=10)
    return BelinkChatAnswer.model_validate(result.final_output), "connected"
