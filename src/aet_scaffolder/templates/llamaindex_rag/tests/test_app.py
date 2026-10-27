"""Generated LlamaIndex RAG API: actual native retrieval and safe offline responses."""
import pytest
from fastapi.testclient import TestClient

from app import providers
from app.main import app

client = TestClient(app)


def test_health_and_ready_mock(monkeypatch):
    monkeypatch.setenv("AET_PROVIDER", "mock")
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ready"}


def test_actual_native_keyword_index_finds_return_passage(monkeypatch):
    monkeypatch.setenv("AET_PROVIDER", "mock")
    result = client.post("/ask", json={"question": "What is the sample return policy?"})
    assert result.status_code == 200, result.text
    data = result.json()
    assert "returns" in data["source_ids"]
    assert "30 days" in data["answer"]
    assert "[returns]" in data["answer"]


def test_no_match_is_deterministic_and_does_not_invoke_model(monkeypatch):
    monkeypatch.setenv("AET_PROVIDER", "openai")
    def forbidden(_):
        raise AssertionError("Model must not be called for zero retrieval matches")
    monkeypatch.setattr(providers, "create_llm", forbidden)
    response = client.post("/ask", json={"question": "astrophysics nebula"})
    assert response.status_code == 200, response.text
    assert response.json()["source_ids"] == []
    assert "No relevant passages" in response.json()["answer"]


def test_provider_call_is_evidence_grounded_with_injected_fake(monkeypatch):
    monkeypatch.setenv("AET_PROVIDER", "openai")
    monkeypatch.setenv("AET_OPENAI_MODEL", "test-model")
    seen = {"count": 0}

    class FakeLLM:
        def complete(self, prompt):
            seen["count"] += 1
            seen["prompt"] = prompt
            return type("Response", (), {"text": "The example return window is 30 days [returns]."})()

    monkeypatch.setattr(providers, "create_llm", lambda settings: FakeLLM())
    response = client.post("/ask", json={"question": "What is the return policy?"})
    assert response.status_code == 200, response.text
    assert response.json()["answer"] == "The example return window is 30 days [returns]."
    assert "returns" in response.json()["source_ids"]
    assert "[returns]" in seen["prompt"]
    assert "30 days" in seen["prompt"]
    assert seen["count"] == 1


def test_provider_exception_is_sanitised(monkeypatch):
    monkeypatch.setenv("AET_PROVIDER", "openai")
    class PrivateFailingLLM:
        def complete(self, prompt):
            raise RuntimeError("private-token-in-third-party-error")
    monkeypatch.setattr(providers, "create_llm", lambda settings: PrivateFailingLLM())
    response = client.post("/ask", json={"question": "return policy"})
    assert response.status_code == 503
    assert "private-token-in-third-party-error" not in response.text


def test_missing_or_symlink_corpus_is_rejected(monkeypatch, tmp_path):
    monkeypatch.setenv("AET_PROVIDER", "mock")
    monkeypatch.setenv("AET_KNOWLEDGE_PATH", str(tmp_path / "missing.jsonl"))
    response = client.post("/ask", json={"question": "returns"})
    assert response.status_code == 503
    assert "Local knowledge base unavailable" in response.text


@pytest.mark.parametrize("payload", [{}, {"question": ""}, {"question": "x" * 2001}, {"question": 123}])
def test_invalid_request_is_rejected(payload):
    assert client.post("/ask", json=payload).status_code == 422
