"""Validated local-only application configuration."""
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AET_", env_file=".env", extra="ignore")

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    provider: Literal["mock", "ollama", "openai", "azure-openai", "anthropic", "bedrock"] = "__PROVIDER__"
    ollama_model: str = "__OLLAMA_MODEL__"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_timeout_seconds: int = Field(default=90, ge=1, le=300)


    # Cloud inference is strictly opt-in. SDKs discover their own credentials.
    model_timeout_seconds: int = Field(default=90, ge=1, le=300)
    model_max_retries: int = Field(default=2, ge=0, le=5)
    openai_model: str = ""
    azure_openai_deployment: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = ""
    anthropic_model: str = ""
    bedrock_model_id: str = ""
    aws_region: str = ""

    @field_validator("azure_openai_endpoint")
    @classmethod
    def validate_azure_endpoint(cls, value: str) -> str:
        if not value:
            return value
        url = urlsplit(value)
        if (url.scheme != "https" or not url.hostname or
                url.username is not None or url.password is not None or
                url.path not in {"", "/"} or url.query or url.fragment):
            raise ValueError("Azure OpenAI endpoint must be a bare HTTPS origin")
        return value.rstrip("/")

    @field_validator("ollama_base_url")
    @classmethod
    def require_local_endpoint(cls, value: str) -> str:
        url = urlsplit(value)
        try:
            port = url.port
        except ValueError as exc:
            raise ValueError("invalid Ollama port") from exc
        if (
            url.scheme != "http"
            or url.hostname not in {"localhost", "127.0.0.1", "::1"}
            or url.username is not None
            or url.password is not None
            or url.path not in {"", "/"}
            or url.query
            or url.fragment
            or port is None
        ):
            raise ValueError("Ollama endpoint must be a local HTTP URL with an explicit port")
        return value.rstrip("/")


def get_settings() -> Settings:
    """Read settings each invocation, supporting safe local overrides and tests."""
    return Settings()
