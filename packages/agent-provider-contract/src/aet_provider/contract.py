"""Minimal cross-environment contract for *text-only* inference."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


class ProviderContractError(ValueError):
    """An invalid request, configuration or response violated the provider contract."""


class ProviderUnavailableError(RuntimeError):
    """A configured provider did not produce a usable response."""


@dataclass(frozen=True)
class GenerateRequest:
    prompt: str

    def __post_init__(self) -> None:
        if not isinstance(self.prompt, str) or not self.prompt.strip():
            raise ProviderContractError("prompt must be a nonempty string")
        if len(self.prompt) > 4000:
            raise ProviderContractError("prompt must not exceed 4000 characters")


@dataclass(frozen=True)
class GenerateResponse:
    text: str
    provider: str
    model: str

    def __post_init__(self) -> None:
        for field in ("text", "provider", "model"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ProviderContractError(f"{field} must be a nonempty string")


@runtime_checkable
class TextProvider(Protocol):
    """Compatible providers implement a single synchronous text-generation method."""

    def generate(self, request: GenerateRequest) -> GenerateResponse: ...


def assert_provider_contract(provider: TextProvider, *, expected_provider: str) -> None:
    """Run a lightweight contract probe against an already-configured provider.

    This probe calls the provider and therefore MUST only be used with mock or
    intentionally stubbed providers in automated tests; real model inference is
    opt-in, possibly nondeterministic, and may be billed.
    """
    if not isinstance(provider, TextProvider):
        raise AssertionError("provider does not expose a generate method")
    if not isinstance(expected_provider, str) or not expected_provider:
        raise ValueError("expected_provider must be a nonempty string")
    result = provider.generate(GenerateRequest(prompt="portable contract probe"))
    assert isinstance(result, GenerateResponse), "provider must return GenerateResponse"
    assert result.provider == expected_provider, "provider name mismatch"
    assert bool(result.text.strip()), "provider produced an empty response"
    assert bool(result.model.strip()), "provider did not declare model"
