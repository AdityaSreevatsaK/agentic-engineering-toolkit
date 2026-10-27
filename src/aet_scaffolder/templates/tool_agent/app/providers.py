"""Minimal provider boundary: deterministic mock or an optional local Ollama model."""
import json
from dataclasses import dataclass
from typing import Protocol
from urllib import error as urllib_error
from urllib import request as urllib_request

from .config import Settings


class ProviderError(RuntimeError):
    """Sanitized inference failure for the HTTP layer."""


class TextProvider(Protocol):
    def generate(self, prompt: str) -> str: ...


class MockProvider:
    def generate(self, prompt: str) -> str:
        return f"Mock response to: {prompt}"


@dataclass(frozen=True)
class OllamaProvider:
    model: str
    base_url: str
    timeout_seconds: int

    def generate(self, prompt: str) -> str:
        data = json.dumps({"model": self.model, "prompt": prompt, "stream": False}).encode("utf-8")
        req = urllib_request.Request(
            f"{self.base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib_request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw = response.read(1_000_001)
            if len(raw) > 1_000_000:
                raise ProviderError("Local inference returned an oversized response")
            result = json.loads(raw.decode("utf-8"))
        except (urllib_error.URLError, TimeoutError, OSError) as exc:
            raise ProviderError("Local Ollama is unavailable or returned an HTTP error") from exc
        except (ValueError, UnicodeError) as exc:
            raise ProviderError("Local Ollama returned an invalid JSON response") from exc
        if not isinstance(result, dict) or not isinstance(result.get("response"), str):
            raise ProviderError("Local Ollama response has no text field")
        return result["response"]


def get_provider(settings: Settings) -> TextProvider:
    if settings.provider == "mock":
        return MockProvider()
    if settings.provider == "ollama":
        return OllamaProvider(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            timeout_seconds=settings.ollama_timeout_seconds,
        )
    if settings.provider in {"openai", "azure-openai", "anthropic", "bedrock"}:
        from .cloud_providers import get_cloud_provider
        return get_cloud_provider(settings)
    raise ProviderError("Unsupported provider configuration")
