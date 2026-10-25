"""Environment-controlled runtime; no implicit AWS calls at import time."""
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AET_", env_file=".env", extra="ignore")

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    provider: Literal["mock", "bedrock"] = "__PROVIDER__"
    aws_region: str = Field(default="us-east-1", pattern=r"^[a-z]{2}(-gov)?-[a-z]+-\d+$")
    bedrock_model_id: str = Field(
        default="us.amazon.nova-lite-v1:0",
        min_length=1,
        max_length=160,
        pattern=r"^[a-zA-Z0-9._:/-]+$",
    )


def get_settings() -> Settings:
    """Read settings per call so tests and local environment overrides are honoured."""
    return Settings()
