import importlib

from fastapi.testclient import TestClient

from agent import TravelProfile


def profile(language="fa"):
    return TravelProfile(
        origin="DOH",
        destination_candidates=["Trabzon", "Tbilisi"],
        passport="Iran",
        departure_date="2026-08-06",
        return_date="2026-08-11",
        travelers=2,
        budget_qar=13_500,
        language=language,
    )


def build_client(tmp_path, monkeypatch):
    monkeypatch.setenv("BELINK_AI_DATABASE", str(tmp_path / "privacy.sqlite3"))
    monkeypatch.setenv("BELINK_SESSION_SECRET", "privacy-test-secret")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("BELINK_ENV", raising=False)
    import main
    importlib.reload(main)
    return TestClient(main.app)


def create_identity(client, language="fa"):
    response = client.post("/api/belink-ai/analyze", json=profile(language).model_dump())
    assert response.status_code == 200
    payload = response.json()
    return payload, {"X-Belink-Client": payload["client_token"]}


def test_user_data_export_requires_authentication(tmp_path, monkeypatch):
    client = build_client(tmp_path, monkeypatch)
    assert client.get("/api/belink-ai/user-data").status_code == 401
    assert client.delete("/api/belink-ai/user-data").status_code == 401


def test_export_contains_only_the_authenticated_clients_data(tmp_path, monkeypatch):
    client = build_client(tmp_path, monkeypatch)
    first, first_headers = create_identity(client, "fa")
    second, second_headers = create_identity(client, "en")

    client.post(
        "/api/belink-ai/chat",
        headers=first_headers,
        json={"session_id": first["session_id"], "question": "بودجه چطور است؟"},
    )

    first_export = client.get("/api/belink-ai/user-data", headers=first_headers)
    second_export = client.get("/api/belink-ai/user-data", headers=second_headers)
    assert first_export.status_code == 200
    assert second_export.status_code == 200

    first_data = first_export.json()
    second_data = second_export.json()
    assert first_data["format"] == "safarma-user-data-v2"
    assert first_data["anonymous_client_id"] != second_data["anonymous_client_id"]
    assert len(first_data["trips"]) == 1
    assert len(second_data["trips"]) == 1
    assert first_data["trips"][0]["id"] != second_data["trips"][0]["id"]
    assert len(first_data["conversations"]) == 1
    assert first_data["conversations"][0]["messages"]
    assert second_data["conversations"][0]["messages"] == []
    assert [row["event_type"] for row in first_data["usage_events"]] == ["chat_offline", "analysis_offline"]
    assert [row["event_type"] for row in second_data["usage_events"]] == ["analysis_offline"]
    assert first_data["cached_analyses"] == []
    assert second_data["cached_analyses"] == []


def test_delete_all_data_returns_receipt_and_leaves_empty_export(tmp_path, monkeypatch):
    client = build_client(tmp_path, monkeypatch)
    analyzed, headers = create_identity(client)
    client.post(
        "/api/belink-ai/chat",
        headers=headers,
        json={"session_id": analyzed["session_id"], "question": "بهترین جایگزین چیست؟"},
    )

    deletion = client.delete("/api/belink-ai/user-data", headers=headers)
    assert deletion.status_code == 200
    receipt = deletion.json()
    assert receipt["deleted"] is True
    assert receipt["records"]["trips"] == 1
    assert receipt["records"]["conversations"] == 1
    assert receipt["records"]["usage_events"] == 2

    exported = client.get("/api/belink-ai/user-data", headers=headers)
    assert exported.status_code == 200
    data = exported.json()
    assert data["trips"] == []
    assert data["conversations"] == []
    assert data["usage_events"] == []
    assert data["cached_analyses"] == []
    assert data["preferences"]["accepted_destinations"] == []
