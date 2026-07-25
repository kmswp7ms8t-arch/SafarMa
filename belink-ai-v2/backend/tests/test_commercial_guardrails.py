import importlib

from fastapi.testclient import TestClient

from agent import BelinkChatAnswer, TravelProfile, deterministic_fallback


def profile(*, budget: float = 13_500, language: str = "fa") -> TravelProfile:
    return TravelProfile(
        origin="DOH",
        destination_candidates=["Trabzon", "Tbilisi"],
        passport="Iran",
        residence_country="Qatar",
        residence_status="gcc",
        departure_date="2026-08-06",
        return_date="2026-08-11",
        travelers=2,
        budget_qar=budget,
        trip_style=["nature", "relaxation"],
        language=language,
    )


def build_connected_client(tmp_path, monkeypatch):
    monkeypatch.setenv("BELINK_AI_DATABASE", str(tmp_path / "guardrails.sqlite3"))
    monkeypatch.setenv("BELINK_SESSION_SECRET", "stable-commercial-guardrails-test-secret")
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-not-a-real-key")
    monkeypatch.setenv("BELINK_ANALYSES_PER_DAY", "1")
    monkeypatch.setenv("BELINK_CHATS_PER_DAY", "1")
    monkeypatch.setenv("BELINK_ANALYSIS_CACHE_SECONDS", "900")
    monkeypatch.setenv("BELINK_RATE_LIMIT", "100")
    monkeypatch.setenv("BELINK_RATE_WINDOW_SECONDS", "60")
    monkeypatch.delenv("BELINK_ENV", raising=False)
    import main
    importlib.reload(main)
    return main, TestClient(main.app)


def test_identical_analysis_uses_cache_without_consuming_second_ai_quota(tmp_path, monkeypatch):
    main, client = build_connected_client(tmp_path, monkeypatch)
    calls = {"analysis": 0}

    async def fake_analyze(value):
        calls["analysis"] += 1
        return deterministic_fallback(value), "connected"

    monkeypatch.setattr(main, "analyze_travel", fake_analyze)

    first_response = client.post("/api/belink-ai/analyze", json=profile().model_dump())
    assert first_response.status_code == 200
    first = first_response.json()
    assert first["cache_hit"] is False
    assert first["usage"]["analyses"]["used"] == 1
    token = first["client_token"]
    headers = {"X-Belink-Client": token}

    second_response = client.post(
        "/api/belink-ai/analyze",
        headers=headers,
        json=profile().model_dump(),
    )
    assert second_response.status_code == 200
    second = second_response.json()
    assert second["cache_hit"] is True
    assert second["usage"]["analyses"]["used"] == 1
    assert second["usage"]["analyses"]["cache_hits"] == 1
    assert calls["analysis"] == 1

    changed = client.post(
        "/api/belink-ai/analyze",
        headers=headers,
        json=profile(budget=14_000).model_dump(),
    )
    assert changed.status_code == 429
    assert "Daily Belink AI analysis limit reached" in changed.json()["detail"]
    assert int(changed.headers["retry-after"]) > 0


def test_chat_quota_and_usage_endpoint_are_client_scoped(tmp_path, monkeypatch):
    main, client = build_connected_client(tmp_path, monkeypatch)

    async def fake_analyze(value):
        return deterministic_fallback(value), "connected"

    async def fake_chat(_profile, _decision, question, _history):
        return BelinkChatAnswer(answer=f"Answer: {question}", verification_status="estimated"), "connected"

    monkeypatch.setattr(main, "analyze_travel", fake_analyze)
    monkeypatch.setattr(main, "chat_with_commander", fake_chat)

    analyzed = client.post("/api/belink-ai/analyze", json=profile().model_dump()).json()
    headers = {"X-Belink-Client": analyzed["client_token"]}

    first_chat = client.post(
        "/api/belink-ai/chat",
        headers=headers,
        json={"session_id": analyzed["session_id"], "question": "What is the main risk?"},
    )
    assert first_chat.status_code == 200
    assert first_chat.json()["usage"]["chats"]["used"] == 1

    second_chat = client.post(
        "/api/belink-ai/chat",
        headers=headers,
        json={"session_id": analyzed["session_id"], "question": "And the budget?"},
    )
    assert second_chat.status_code == 429
    assert "Daily Belink AI chat limit reached" in second_chat.json()["detail"]

    usage = client.get("/api/belink-ai/usage", headers=headers)
    assert usage.status_code == 200
    payload = usage.json()
    assert payload["analyses"]["used"] == 1
    assert payload["chats"]["used"] == 1
    assert payload["analyses"]["limit"] == 1
    assert payload["chats"]["limit"] == 1

    other = client.post("/api/belink-ai/analyze", json=profile(language="en").model_dump())
    assert other.status_code == 200
    other_headers = {"X-Belink-Client": other.json()["client_token"]}
    other_usage = client.get("/api/belink-ai/usage", headers=other_headers).json()
    assert other_usage["analyses"]["used"] == 1
    assert other_usage["chats"]["used"] == 0


def test_export_and_delete_include_usage_and_cached_analysis(tmp_path, monkeypatch):
    main, client = build_connected_client(tmp_path, monkeypatch)

    async def fake_analyze(value):
        return deterministic_fallback(value), "connected"

    monkeypatch.setattr(main, "analyze_travel", fake_analyze)

    analyzed = client.post("/api/belink-ai/analyze", json=profile().model_dump()).json()
    headers = {"X-Belink-Client": analyzed["client_token"]}

    exported = client.get("/api/belink-ai/user-data", headers=headers)
    assert exported.status_code == 200
    data = exported.json()
    assert data["format"] == "safarma-user-data-v2"
    assert len(data["usage_events"]) == 1
    assert data["usage_events"][0]["event_type"] == "analysis"
    assert len(data["cached_analyses"]) == 1

    deleted = client.delete("/api/belink-ai/user-data", headers=headers)
    assert deleted.status_code == 200
    receipt = deleted.json()["records"]
    assert receipt["usage_events"] == 1
    assert receipt["cached_analyses"] == 1

    empty = client.get("/api/belink-ai/user-data", headers=headers).json()
    assert empty["trips"] == []
    assert empty["conversations"] == []
    assert empty["usage_events"] == []
    assert empty["cached_analyses"] == []
