"""Local-only transport and failure tests; never contact an actual Ollama service."""
import json
from urllib.error import URLError

import pytest

from aet_provider import (
    GenerateRequest, LegacyTextAdapter, MockProvider, OllamaProvider,
    ProviderContractError, ProviderUnavailableError, assert_provider_contract,
)


def transport_ok(request, timeout):
    assert request.method == "POST"
    assert request.full_url == "http://127.0.0.1:11434/api/generate"
    assert request.get_header("Content-type") == "application/json"
    assert timeout == 90
    payload = json.loads(request.data.decode("utf-8"))
    assert payload == {"model": "tiny-test:1b", "prompt": "portable contract probe", "stream": False}
    return b'{"response":"Synthetic Ollama response"}'


def test_ollama_passes_contract_with_fake_transport():
    provider = OllamaProvider(model="tiny-test:1b", transport=transport_ok)
    assert_provider_contract(provider, expected_provider="ollama")


def test_ollama_actual_prompt_forwarded_unchanged():
    seen = []

    def capture(req, timeout):
        seen.append(json.loads(req.data)["prompt"])
        return b'{"response":"hello from fake Ollama"}'

    result = OllamaProvider(transport=capture).generate(GenerateRequest("preserve THIS"))
    assert seen == ["preserve THIS"]
    assert result.text == "hello from fake Ollama"
    assert result.provider == "ollama"


@pytest.mark.parametrize("base", [
    "https://localhost:11434", "http://example.com:11434",
    "http://127.0.0.1:11434/extra", "http://localhost:11434?remote=true",
    "http://user:pwd@localhost:11434", "http://localhost",
    "http://localhost:invalid", "http://127.0.0.1:11434#fragment",
])
def test_only_loopback_http_with_port_allowed(base):
    with pytest.raises(ProviderContractError):
        OllamaProvider(base_url=base)


@pytest.mark.parametrize("model", ["", "contains spaces", "bad\nheader", "../bad"])
def test_invalid_model_rejected(model):
    with pytest.raises(ProviderContractError):
        OllamaProvider(model=model)


@pytest.mark.parametrize("timeout", [0, -1, 301, "fast", True])
def test_invalid_timeout_rejected(timeout):
    with pytest.raises(ProviderContractError):
        OllamaProvider(timeout_seconds=timeout)


@pytest.mark.parametrize(
    "payload",
    [
        b"", b"not JSON", b"{}", b"[]", b'{"response":null}',
        b'{"response":""}', b"x" * 1_000_001,
    ],
    ids=["empty", "malformed", "object-missing-response", "array", "null-response", "empty-text", "oversized"],
)
def test_malformed_response_is_sanitized(payload):
    provider = OllamaProvider(transport=lambda *args: payload)
    with pytest.raises(ProviderUnavailableError):
        provider.generate(GenerateRequest("hello"))


def test_network_failure_is_sanitized():
    def fails(request, timeout):
        raise URLError("private endpoint details")

    provider = OllamaProvider(transport=fails)
    with pytest.raises(ProviderUnavailableError, match="unavailable") as exc:
        provider.generate(GenerateRequest("hello"))
    assert "private endpoint details" not in str(exc.value)


def test_legacy_bridge_is_compatible_with_text_generators():
    class OldStyle:
        def generate(self, prompt):
            return f"Mock response to: {prompt}"

    bridge = LegacyTextAdapter(OldStyle(), name="legacy-mock", model="old")
    assert_provider_contract(bridge, expected_provider="legacy-mock")
    assert bridge.generate(GenerateRequest("hi")).text == "Mock response to: hi"


def test_legacy_failure_is_sanitized():
    class Broken:
        def generate(self, prompt):
            raise RuntimeError("private credentials in error")

    bridge = LegacyTextAdapter(Broken())
    with pytest.raises(ProviderUnavailableError) as exc:
        bridge.generate(GenerateRequest("anything"))
    assert "private credentials" not in str(exc.value)


def test_no_sdk_needed_for_mock():
    assert isinstance(MockProvider().generate(GenerateRequest("ok")).text, str)
