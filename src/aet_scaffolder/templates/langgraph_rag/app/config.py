"""Validated local-first configuration for the generated RAG service."""
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AET_", env_file=".env", extra="ignore")

    provider: Literal["mock", "ollama"] = "__PROVIDER__"
    ollama_model: str = "__OLLAMA_MODEL__"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_timeout_seconds: int = Field(default=90, ge=1, le=300)
    knowledge_path: str = "data/knowledge.jsonl"
    top_k: int = Field(default=2, ge=1, le=5)

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
            or url.username is not None or url.password is not None
            or url.path not in {"", "/"} or url.query or url.fragment
            or port is None
        ):
            raise ValueError("Ollama endpoint must be a local HTTP URL with an explicit port")
        return value.rstrip("/")


def get_settings() -> Settings:
    return Settings()
