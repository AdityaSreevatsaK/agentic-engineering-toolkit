"""Native, lazy Strands model adapters for optional hosted inference.

OpenAI and Anthropic SDKs resolve API keys via their standard process environment.
Azure uses the official AsyncAzureOpenAI client injected into Strands' OpenAIModel.
No credential values are persisted or embedded in the generated project.
"""
from .config import Settings


def _required(value: str, field: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"Missing required {field} configuration")
    return value


def create_cloud_model(settings: Settings):
    """Construct only the explicitly chosen provider. No inference during setup."""
    if settings.provider == "openai":
        try:
            from strands.models.openai import OpenAIModel
        except ImportError as exc:
            raise RuntimeError("Optional Strands OpenAI integration is not installed") from exc
        return OpenAIModel(model_id=_required(settings.openai_model, "OpenAI model"))

    if settings.provider == "anthropic":
        try:
            from strands.models.anthropic import AnthropicModel
        except ImportError as exc:
            raise RuntimeError("Optional Strands Anthropic integration is not installed") from exc
        return AnthropicModel(
            model_id=_required(settings.anthropic_model, "Anthropic model"),
            max_tokens=settings.anthropic_max_tokens,
        )

    if settings.provider == "azure-openai":
        try:
            from openai import AsyncAzureOpenAI
            from strands.models.openai import OpenAIModel
        except ImportError as exc:
            raise RuntimeError("Optional Strands Azure OpenAI integration is not installed") from exc
        deployment = _required(settings.azure_openai_deployment, "Azure deployment")
        endpoint = _required(settings.azure_openai_endpoint, "Azure endpoint")
        api_version = _required(settings.azure_openai_api_version, "Azure API version")
        # Native Azure SDK reads AZURE_OPENAI_API_KEY / AZURE_OPENAI_AD_TOKEN,
        # or another supported credential mechanism configured by the user.
        client = AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            api_version=api_version,
            azure_deployment=deployment,
        )
        return OpenAIModel(model_id=deployment, client=client)

    raise ValueError("Unsupported Strands model provider")
