"""FastAPI smoke tests use the real Strands Agent with an offline provider."""
import pytest
from fastapi.testclient import TestClient

from app import agent as agent_module
from app.main import app

client = TestClient(app)


def test_health_is_liveness_only():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_offline_end_to_end_tool_call(monkeypatch):
    monkeypatch.setenv("AET_PROVIDER", "mock")
    result = client.post("/invoke", json={"question": "order status ORD-1001"})
    assert result.status_code == 200, result.text
    data = result.json()
    assert data["provider"] == "mock"
    assert data["tool_used"] is True
    assert "shipped" in data["answer"].lower()


def test_offline_arbitrary_question_does_not_use_tool(monkeypatch):
    monkeypatch.setenv("AET_PROVIDER", "mock")
    data = client.post("/invoke", json={"question": "hello"}).json()
    assert data["tool_used"] is False
    assert data["provider"] == "mock"


def test_aws_failure_never_leaks_exception_details(monkeypatch):
    monkeypatch.setenv("AET_PROVIDER", "bedrock")

    def raise_private(*args, **kwargs):
        raise RuntimeError("AWS secret details should never be sent to callers")

    monkeypatch.setattr(agent_module, "BedrockModel", raise_private)
    response = client.post("/invoke", json={"question": "hello"})
    assert response.status_code == 503
    assert "AWS secret details" not in response.text


@pytest.mark.parametrize("body", [{}, {"question": ""}, {"question": "x" * 1001},
                                     {"question": 123}])
def test_invalid_requests_are_rejected(body):
    response = client.post("/invoke", json=body)
    assert response.status_code == 422
