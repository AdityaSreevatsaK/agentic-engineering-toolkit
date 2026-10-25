"""Optional loopback-only Ollama text generation; mock mode uses retrieved evidence."""
import json
from dataclasses import dataclass
from urllib import error as urllib_error
from urllib import request as urllib_request

from .config import Settings


class ProviderError(RuntimeError):
    """Sanitised model-provider error."""


@dataclass(frozen=True)
class OllamaProvider:
    model: str
    base_url: str
    timeout_seconds: int

    def generate(self, prompt: str) -> str:
        data = json.dumps({"model": self.model, "prompt": prompt, "stream": False}).encode("utf-8")
        request = urllib_request.Request(
            f"{self.base_url}/api/generate", data=data,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urllib_request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = response.read(1_000_001)
            if len(payload) > 1_000_000:
                raise ProviderError("Local inference returned an oversized response")
            result = json.loads(payload.decode("utf-8"))
        except (urllib_error.URLError, TimeoutError, OSError) as exc:
            raise ProviderError("Local Ollama is unavailable") from exc
        except (UnicodeError, ValueError) as exc:
            raise ProviderError("Local Ollama returned an invalid response") from exc
        if not isinstance(result, dict) or not isinstance(result.get("response"), str):
            raise ProviderError("Local Ollama returned no text response")
        return result["response"]


def get_provider(settings: Settings) -> OllamaProvider:
    if settings.provider != "ollama":
        raise ProviderError("Live generation requires the local Ollama provider")
    return OllamaProvider(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        timeout_seconds=settings.ollama_timeout_seconds,
    )
