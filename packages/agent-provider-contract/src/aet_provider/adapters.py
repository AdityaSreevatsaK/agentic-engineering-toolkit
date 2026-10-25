"""Mock, loopback Ollama and compatibility bridge reference implementations."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Callable, Protocol
from urllib import error as urllib_error, request as urllib_request
from urllib.parse import urlsplit

from .contract import (
    GenerateRequest,
    GenerateResponse,
    ProviderContractError,
    ProviderUnavailableError,
)

_MODEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_MAX_BYTES = 1_000_000


@dataclass(frozen=True)
class MockProvider:
    """A deterministic local reference, no network or model downloads."""

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        if not isinstance(request, GenerateRequest):
            raise ProviderContractError("request must be GenerateRequest")
        return GenerateResponse(
            text=f"Mock response to: {request.prompt}", provider="mock", model="deterministic-mock"
        )


def _local_url(base_url: str) -> str:
    if not isinstance(base_url, str):
        raise ProviderContractError("Ollama endpoint must be a URL string")
    try:
        parts = urlsplit(base_url)
        port = parts.port
    except ValueError as exc:
        raise ProviderContractError("invalid Ollama endpoint") from exc
    if (
        parts.scheme != "http"
        or parts.hostname not in {"localhost", "127.0.0.1", "::1"}
        or port is None
        or parts.username is not None
        or parts.password is not None
        or parts.path not in {"", "/"}
        or parts.query
        or parts.fragment
    ):
        raise ProviderContractError("Ollama endpoint must be loopback HTTP with an explicit port")
    return base_url.rstrip("/")


def _default_transport(request: urllib_request.Request, timeout: float) -> bytes:
    with urllib_request.urlopen(request, timeout=timeout) as response:
        return response.read(_MAX_BYTES + 1)


@dataclass(frozen=True)
class OllamaProvider:
    """Optional *local* Ollama text adapter; not an LLM tool-calling implementation."""

    model: str = "llama3.2:1b"
    base_url: str = "http://127.0.0.1:11434"
    timeout_seconds: float = 90.0
    transport: Callable[[urllib_request.Request, float], bytes] = field(
        default=_default_transport, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        if not isinstance(self.model, str) or not _MODEL.fullmatch(self.model):
            raise ProviderContractError("invalid local model identifier")
        if isinstance(self.timeout_seconds, bool) or not isinstance(self.timeout_seconds, (int, float)):
            raise ProviderContractError("timeout must be a positive number")
        if not 0 < self.timeout_seconds <= 300:
            raise ProviderContractError("timeout must be in (0, 300]")
        if not callable(self.transport):
            raise ProviderContractError("transport must be callable")
        object.__setattr__(self, "base_url", _local_url(self.base_url))

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        if not isinstance(request, GenerateRequest):
            raise ProviderContractError("request must be GenerateRequest")
        payload = json.dumps({
            "model": self.model, "prompt": request.prompt, "stream": False
        }).encode("utf-8")
        http_request = urllib_request.Request(
            self.base_url + "/api/generate",
            data=payload, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            raw = self.transport(http_request, float(self.timeout_seconds))
        except (urllib_error.URLError, TimeoutError, OSError) as exc:
            raise ProviderUnavailableError("Local Ollama inference is unavailable") from exc
        if not isinstance(raw, bytes) or len(raw) > _MAX_BYTES:
            raise ProviderUnavailableError("Local Ollama returned an invalid or oversized payload")
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeError, ValueError) as exc:
            raise ProviderUnavailableError("Local Ollama returned invalid JSON") from exc
        if not isinstance(decoded, dict) or not isinstance(decoded.get("response"), str):
            raise ProviderUnavailableError("Local Ollama response has no text field")
        try:
            return GenerateResponse(text=decoded["response"], provider="ollama", model=self.model)
        except ProviderContractError as exc:
            raise ProviderUnavailableError("Local Ollama returned empty text") from exc


class LegacyTextProvider(Protocol):
    """Existing generated AET provider duck type: generate(str) -> str."""

    def generate(self, prompt: str) -> str: ...


@dataclass(frozen=True)
class LegacyTextAdapter:
    """Compatibility bridge without importing the scaffolder or LangGraph."""

    delegate: LegacyTextProvider
    name: str = "legacy"
    model: str = "legacy-text"

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        if not isinstance(request, GenerateRequest):
            raise ProviderContractError("request must be GenerateRequest")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ProviderContractError("provider name must be nonempty")
        try:
            text = self.delegate.generate(request.prompt)
        except Exception as exc:
            raise ProviderUnavailableError("Legacy text provider failed") from exc
        return GenerateResponse(text=text, provider=self.name, model=self.model)
