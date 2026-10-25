"""RAG API tests cover retrieval, mocked generation and sanitised errors."""
import io
import json

import pytest
from fastapi.testclient import TestClient

from app import providers
from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_retrieval_grounded_mock_response(monkeypatch):
    monkeypatch.setenv("AET_PROVIDER", "mock")
    response = client.post("/ask", json={"question": "What is the return policy?"})
    assert response.status_code == 200
    body = response.json()
    assert body["source_ids"][0] == "returns"
    assert "[returns]" in body["answer"]
    assert "30 days" in body["answer"]


def test_no_relevant_passages(monkeypatch):
    monkeypatch.setenv("AET_PROVIDER", "mock")
    response = client.post("/ask", json={"question": "astrophysics nebula"})
    assert response.status_code == 200
    assert response.json()["source_ids"] == []
    assert "No relevant passages" in response.json()["answer"]


def test_mock_does_not_call_local_model(monkeypatch):
    monkeypatch.setenv("AET_PROVIDER", "mock")
    def unexpected(*args, **kwargs):
        raise AssertionError("Mock should never use HTTP")
    monkeypatch.setattr(providers.urllib_request, "urlopen", unexpected)
    assert client.post("/ask", json={"question": "return policy"}).status_code == 200


def test_ollama_receives_retrieved_source_and_uses_fake_transport(monkeypatch):
    monkeypatch.setenv("AET_PROVIDER", "ollama")
    monkeypatch.setenv("AET_OLLAMA_MODEL", "tiny-test:1b")
    observed = {}

    def fake_open(req, timeout):
        observed["url"] = req.full_url
        observed["body"] = json.loads(req.data.decode("utf-8"))
        observed["timeout"] = timeout
        return io.BytesIO(json.dumps({"response": "Sample returns are allowed [returns]."}).encode())

    monkeypatch.setattr(providers.urllib_request, "urlopen", fake_open)
    result = client.post("/ask", json={"question": "What is the return policy?"})
    assert result.status_code == 200
    assert result.json()["answer"] == "Sample returns are allowed [returns]."
    assert "returns" in result.json()["source_ids"]
    assert observed["url"] == "http://127.0.0.1:11434/api/generate"
    assert "30 days" in observed["body"]["prompt"]
    assert observed["body"]["model"] == "tiny-test:1b"


def test_ollama_failure_is_sanitised(monkeypatch):
    monkeypatch.setenv("AET_PROVIDER", "ollama")

    def fail(*args, **kwargs):
        raise providers.urllib_error.URLError("private local exception context")

    monkeypatch.setattr(providers.urllib_request, "urlopen", fail)
    response = client.post("/ask", json={"question": "return policy"})
    assert response.status_code == 503
    assert "private local exception context" not in response.text


def test_missing_corpus_is_sanitised(monkeypatch, tmp_path):
    monkeypatch.setenv("AET_KNOWLEDGE_PATH", str(tmp_path / "missing.jsonl"))
    response = client.post("/ask", json={"question": "return policy"})
    assert response.status_code == 503
    assert "Local knowledge base unavailable" in response.text


@pytest.mark.parametrize("payload", [{}, {"question": ""}, {"question": "x" * 2001}, {"question": 123}])
def test_invalid_requests(payload):
    assert client.post("/ask", json=payload).status_code == 422
