"""Offline contract tests; these cover protocol behavior, not live model quality."""
import pytest

from aet_provider import (
    GenerateRequest, GenerateResponse, ProviderContractError,
    MockProvider, assert_provider_contract,
)


def test_mock_contract_probe_and_explicit_response():
    provider = MockProvider()
    assert_provider_contract(provider, expected_provider="mock")
    result = provider.generate(GenerateRequest("hello"))
    assert result == GenerateResponse(
        text="Mock response to: hello", provider="mock", model="deterministic-mock"
    )


@pytest.mark.parametrize("prompt", ["", "   ", 5, None, "x" * 4001])
def test_bad_requests_are_rejected(prompt):
    with pytest.raises(ProviderContractError):
        GenerateRequest(prompt)


@pytest.mark.parametrize("kwargs", [
    {"text": "", "provider": "mock", "model": "m"},
    {"text": "ok", "provider": "", "model": "m"},
    {"text": "ok", "provider": "mock", "model": ""},
    {"text": 42, "provider": "mock", "model": "m"},
])
def test_invalid_responses_are_rejected(kwargs):
    with pytest.raises(ProviderContractError):
        GenerateResponse(**kwargs)


def test_mismatched_provider_fails_contract():
    with pytest.raises(AssertionError, match="mismatch"):
        assert_provider_contract(MockProvider(), expected_provider="ollama")


def test_provider_without_generate_fails_contract():
    with pytest.raises(AssertionError, match="generate"):
        assert_provider_contract(object(), expected_provider="mock")


def test_wrong_request_object_fails():
    with pytest.raises(ProviderContractError):
        MockProvider().generate("hello")
