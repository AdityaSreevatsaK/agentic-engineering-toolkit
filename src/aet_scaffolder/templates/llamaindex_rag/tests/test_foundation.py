"""Generated-app foundation tests: readiness, request IDs, and log privacy."""
import json
import re

from fastapi.testclient import TestClient

from app import foundation
from app.main import app

client = TestClient(app)


def test_health_is_liveness_only():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_offline_provider_is_ready(monkeypatch):
    monkeypatch.setenv("AET_PROVIDER", "mock")
    result = client.get("/ready")
    assert result.status_code == 200
    assert result.json() == {"status": "ready"}


def test_invalid_provider_configuration_is_not_disclosed(monkeypatch):
    monkeypatch.setenv("AET_PROVIDER", "not-a-real-provider")
    result = client.get("/ready")
    assert result.status_code == 503
    assert "not-a-real-provider" not in result.text


def test_server_issued_request_id_and_redacted_structured_log(monkeypatch):
    events = []
    monkeypatch.setattr(foundation._LOGGER, "info", events.append)
    monkeypatch.setenv("AET_LOG_LEVEL", "INFO")
    response = client.get(
        "/health?token=top-secret-query",
        headers={"X-Request-ID": "client-controlled-id",
                 "Authorization": "Bearer top-secret-header"},
    )
    assert response.status_code == 200
    identifier = response.headers["X-Request-ID"]
    assert re.fullmatch(r"[a-f0-9]{32}", identifier)
    assert identifier != "client-controlled-id"
    assert len(events) == 1
    payload = json.loads(events[0])
    assert payload["event"] == "request_completed"
    assert payload["request_id"] == identifier
    assert payload["route"] == "/health"
    assert payload["status_code"] == 200
    assert payload["duration_ms"] >= 0
    assert "top-secret" not in events[0]
    assert "Authorization" not in events[0]


def test_unknown_path_is_not_logged_verbatim(monkeypatch):
    events = []
    monkeypatch.setattr(foundation._LOGGER, "info", events.append)
    response = client.get("/secret-document-123")
    assert response.status_code == 404
    assert json.loads(events[0])["route"] == "<unmatched>"
    assert "secret-document-123" not in events[0]


def test_live_provider_is_not_claimed_ready(monkeypatch):
    from app.config import Settings
    values = Settings.model_fields["provider"].annotation.__args__
    live = "bedrock" if "bedrock" in values else "ollama"
    monkeypatch.setenv("AET_PROVIDER", live)
    response = client.get("/ready")
    assert response.status_code == 503
    assert "Live" in response.json()["detail"]


def test_unexpected_exception_is_sanitised(monkeypatch):
    events = []
    monkeypatch.setattr(foundation._LOGGER, "info", events.append)

    @app.get("/__internal_test_failure")
    def crash_for_test():
        raise RuntimeError("a-private-secret")

    response = client.get("/__internal_test_failure")
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "a-private-secret" not in response.text
    event = json.loads(events[-1])
    assert event["event"] == "request_failed"
    assert event["route"] == "<unmatched>"
    assert "a-private-secret" not in events[-1]
