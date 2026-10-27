"""Optional LangChain-native cloud chat models; no SDK imported in mock/Ollama mode.

Credentials are resolved by each provider's official SDK, never stored by AET.
"""
import os
from dataclasses import dataclass
from typing import Any

from .config import Settings
from .providers import ProviderError


def _required(value: str, name: str) -> str:
    value = value.strip()
    if not value:
        raise ProviderError(f"Missing required {name} configuration")
    return value


def _make_model(settings: Settings) -> Any:
    """Instantiate only the explicitly selected provider; does not invoke it."""
    timeout = settings.model_timeout_seconds
    retries = settings.model_max_retries
    try:
        if settings.provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=_required(settings.openai_model, "OpenAI model"),
                timeout=timeout, max_retries=retries,
            )
        if settings.provider == "azure-openai":
            from langchain_openai import AzureChatOpenAI
            return AzureChatOpenAI(
                azure_deployment=_required(settings.azure_openai_deployment, "Azure deployment"),
                azure_endpoint=_required(settings.azure_openai_endpoint, "Azure endpoint"),
                api_version=_required(settings.azure_openai_api_version, "Azure API version"),
                timeout=timeout, max_retries=retries,
            )
        if settings.provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=_required(settings.anthropic_model, "Anthropic model"),
                timeout=timeout, max_retries=retries,
            )
        if settings.provider == "bedrock":
            from langchain_aws import ChatBedrock
            kwargs: dict[str, Any] = {
                "model_id": _required(settings.bedrock_model_id, "Bedrock model ID"),
            }
            region = (settings.aws_region or os.environ.get("AWS_REGION")
                      or os.environ.get("AWS_DEFAULT_REGION"))
            if region:
                kwargs["region_name"] = region
            return ChatBedrock(**kwargs)
    except ProviderError:
        raise
    except ImportError as exc:
        raise ProviderError("Selected cloud provider integration is not installed") from exc
    except Exception as exc:
        # API keys, endpoints, exception payloads and SDK diagnostics are never
        # copied into HTTP responses or structured request logs.
        raise ProviderError("Cloud provider initialisation failed") from exc
    raise ProviderError("Unsupported cloud provider configuration")


@dataclass(frozen=True)
class CloudChatProvider:
    model: Any

    def generate(self, prompt: str) -> str:
        try:
            message = self.model.invoke(prompt)
            content = message.content
        except Exception as exc:
            raise ProviderError("Cloud model invocation failed") from exc

        if isinstance(content, str):
            answer = content
        elif isinstance(content, list):
            # Some chat APIs return text alongside non-text content blocks.
            answer = "".join(
                block["text"] for block in content
                if isinstance(block, dict) and isinstance(block.get("text"), str)
                and block.get("type", "text") == "text"
            )
        else:
            answer = ""
        if not answer or len(answer) > 1_000_000:
            raise ProviderError("Cloud model returned an empty or oversized text response")
        return answer


def get_cloud_provider(settings: Settings) -> CloudChatProvider:
    return CloudChatProvider(model=_make_model(settings))
