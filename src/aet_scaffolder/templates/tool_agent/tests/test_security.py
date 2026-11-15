"""Opt-in production boundary tests, fully offline and without provider calls."""
import json

from fastapi.testclient import TestClient

from app import foundation
from app.main import app

client = TestClient(app)
ENDPOINT = "/ask" if any(route.path == "/ask" for route in app.routes) else "/invoke"
KEY = "test-only-tenant-key-not-for-production-0123456789"


def test_hardened_requires_valid_keys(monkeypatch):
    monkeypatch.setenv("AET_SECURITY_MODE", "hardened")
    monkeypatch.delenv("AET_TENANT_KEYS_JSON", raising=False)
    assert client.get("/ready").status_code == 503
    response = client.post(ENDPOINT, json={"question": "hello"})
    assert response.status_code == 503
    assert "key" not in response.text.lower()


def test_hardened_denies_missing_and_wrong_bearer(monkeypatch):
    monkeypatch.setenv("AET_PROVIDER", "mock")
    monkeypatch.setenv("AET_SECURITY_MODE", "hardened")
    monkeypatch.setenv("AET_TENANT_KEYS_JSON", json.dumps({"alpha": KEY}))
    missing = client.post(ENDPOINT, json={"question": "hello"})
    wrong = client.post(
        ENDPOINT, json={"question": "hello"},
        headers={"Authorization": "Bearer wrong"},
    )
    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert "WWW-Authenticate" in missing.headers
    assert KEY not in missing.text + wrong.text


def test_hardened_rate_limit_is_per_tenant(monkeypatch):
    monkeypatch.setenv("AET_PROVIDER", "mock")
    monkeypatch.setenv("AET_SECURITY_MODE", "hardened")
    monkeypatch.setenv("AET_TENANT_KEYS_JSON", json.dumps({"rate_test": KEY}))
    monkeypatch.setenv("AET_TENANT_RATE_PER_MINUTE", "1")
    with foundation._LOCK:
        foundation._GLOBAL_REQUESTS.clear()
        foundation._TENANT_REQUESTS.clear()
        foundation._TENANT_IN_FLIGHT.clear()
    headers = {"Authorization": "Bearer " + KEY}
    first = client.post(ENDPOINT, json={"question": "returns"}, headers=headers)
    second = client.post(ENDPOINT, json={"question": "returns"}, headers=headers)
    assert first.status_code != 429
    assert second.status_code == 429
    assert second.headers["Retry-After"] == "60"


def test_unauthenticated_live_provider_rejects_remote_client(monkeypatch):
    from app.config import Settings
    values = Settings.model_fields["provider"].annotation.__args__
    live = "bedrock" if "bedrock" in values else "ollama"
    monkeypatch.setenv("AET_PROVIDER", live)
    monkeypatch.setenv("AET_SECURITY_MODE", "local")
    monkeypatch.setattr(foundation, "_is_loopback_client", lambda request: False)
    response = client.post(ENDPOINT, json={"question": "hello"})
    assert response.status_code == 403


def test_unknown_security_profile_fails_closed(monkeypatch):
    monkeypatch.setenv("AET_SECURITY_MODE", "unrecognised")
    monkeypatch.setenv("AET_PROVIDER", "mock")
    assert client.post(ENDPOINT, json={"question": "hello"}).status_code == 503
