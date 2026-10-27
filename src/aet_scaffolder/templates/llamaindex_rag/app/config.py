"""Validated, environment-driven LlamaIndex RAG configuration."""
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AET_", env_file=".env", extra="ignore")

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    provider: Literal[
        "mock", "ollama", "openai", "azure-openai", "anthropic", "bedrock"
    ] = "__PROVIDER__"
    knowledge_path: str = "data/knowledge.jsonl"
    top_k: int = Field(default=2, ge=1, le=5)
    ollama_model: str = "__OLLAMA_MODEL__"
    ollama_base_url: str = "http://127.0.0.1:11434"
    model_timeout_seconds: int = Field(default=90, ge=1, le=300)
    openai_model: str = ""
    azure_openai_model: str = ""
    azure_openai_deployment: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = ""
    anthropic_model: str = ""
    bedrock_model_id: str = ""
    aws_region: str = ""

    @field_validator("ollama_base_url")
    @classmethod
    def validate_ollama_url(cls, value: str) -> str:
        url = urlsplit(value)
        try:
            port = url.port
        except ValueError as exc:
            raise ValueError("Invalid Ollama port") from exc
        if (
            url.scheme != "http" or url.hostname not in {"127.0.0.1", "localhost", "::1"}
            or port is None or url.username or url.password
            or url.path not in {"", "/"} or url.query or url.fragment
        ):
            raise ValueError("Ollama URL must use local loopback HTTP with an explicit port")
        return value.rstrip("/")

    @field_validator("azure_openai_endpoint")
    @classmethod
    def validate_azure_endpoint(cls, value: str) -> str:
        if not value:
            return value
        url = urlsplit(value)
        try:
            port = url.port
        except ValueError as exc:
            raise ValueError("Invalid Azure endpoint port") from exc
        if (
            url.scheme != "https" or not url.hostname
            or url.username or url.password or port not in {None, 443}
            or url.path not in {"", "/"} or url.query or url.fragment
        ):
            raise ValueError("Azure OpenAI endpoint must be a bare HTTPS origin")
        return value.rstrip("/")


def get_settings() -> Settings:
    return Settings()
