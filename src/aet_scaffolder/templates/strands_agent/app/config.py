"""Environment-controlled runtime; no implicit AWS calls at import time."""
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AET_", env_file=".env", extra="ignore")

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    provider: Literal["mock", "bedrock", "openai", "azure-openai", "anthropic"] = "__PROVIDER__"
    aws_region: str = Field(default="us-east-1", pattern=r"^[a-z]{2}(-gov)?-[a-z]+-\d+$")
    # Cloud models are always opt-in; native SDKs source credentials from environment.
    openai_model: str = Field(default="", max_length=160)
    anthropic_model: str = Field(default="", max_length=160)
    anthropic_max_tokens: int = Field(default=1024, ge=64, le=4096)
    azure_openai_deployment: str = Field(default="", max_length=160)
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = Field(default="", max_length=64)

    @field_validator("azure_openai_endpoint")
    @classmethod
    def validate_azure_endpoint(cls, value: str) -> str:
        if not value:
            return value
        parsed = urlsplit(value)
        try:
            port = parsed.port
        except ValueError as exc:
            raise ValueError("Invalid Azure endpoint port") from exc
        if (
            parsed.scheme != "https" or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.path not in {"", "/"} or parsed.query or parsed.fragment
            or port not in {None, 443}
        ):
            raise ValueError("Azure endpoint must be an HTTPS origin without credentials or paths")
        return value.rstrip("/")

    bedrock_model_id: str = Field(
        default="us.amazon.nova-lite-v1:0",
        min_length=1,
        max_length=160,
        pattern=r"^[a-zA-Z0-9._:/-]+$",
    )


def get_settings() -> Settings:
    """Read settings per call so tests and local environment overrides are honoured."""
    return Settings()
