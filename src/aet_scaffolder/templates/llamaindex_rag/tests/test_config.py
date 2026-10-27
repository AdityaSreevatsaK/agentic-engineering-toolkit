"""Safe environment validation for generated LlamaIndex template."""
import pytest
from pydantic import ValidationError
from app.config import Settings


@pytest.mark.parametrize("invalid", [
    "https://127.0.0.1:11434",
    "http://provider.example.com:11434",
    "http://localhost",
    "http://user:pass@localhost:11434",
    "http://127.0.0.1:11434/api",
])
def test_ollama_must_be_explicit_loopback_http(invalid):
    with pytest.raises(ValidationError):
        Settings(ollama_base_url=invalid)


@pytest.mark.parametrize("invalid", [
    "http://azure.example.com", "https://user:pass@azure.example.com",
    "https://azure.example.com/extra", "https://azure.example.com/?token=secret",
])
def test_azure_requires_bare_https_origin(invalid):
    with pytest.raises(ValidationError):
        Settings(azure_openai_endpoint=invalid)


def test_default_is_mock_without_live_api():
    assert Settings(provider="mock").provider == "mock"
