"""Independent provider and configuration validation tests."""
import io
import json

import pytest
from pydantic import ValidationError

from app import providers
from app.config import Settings


@pytest.mark.parametrize(
    "invalid_url",
    [
        "https://127.0.0.1:11434",
        "http://api.example.com:11434",
        "http://127.0.0.1:11434/remote",
        "http://user:pass@localhost:11434",
        "http://localhost",
    ],
)
def test_remote_or_unsafe_endpoint_rejected(invalid_url):
    with pytest.raises(ValidationError):
        Settings(ollama_base_url=invalid_url)


def test_mock_provider_independent_of_ollama():
    assert providers.get_provider(Settings(provider="mock")).generate("hi") == "Mock response to: hi"


@pytest.mark.parametrize("response", [b"{}", b"not-json", b'{"response":null}'])
def test_invalid_ollama_payload_rejected(monkeypatch, response):
    monkeypatch.setattr(providers.urllib_request, "urlopen", lambda *a, **k: io.BytesIO(response))
    service = providers.get_provider(Settings(provider="ollama"))
    with pytest.raises(providers.ProviderError):
        service.generate("hello")


def test_ollama_payload_is_non_streaming(monkeypatch):
    seen = {}

    def fake_open(req, timeout):
        seen["data"] = json.loads(req.data.decode("utf-8"))
        return io.BytesIO(b'{"response":"fine"}')

    monkeypatch.setattr(providers.urllib_request, "urlopen", fake_open)
    service = providers.get_provider(Settings(provider="ollama", ollama_model="model:1b"))
    assert service.generate("hello") == "fine"
    assert seen["data"]["stream"] is False
