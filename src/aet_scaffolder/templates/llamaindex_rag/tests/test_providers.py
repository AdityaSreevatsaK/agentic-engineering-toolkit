"""Cloud SDK wiring is tested with fake modules, never paid API calls."""
import sys
from types import ModuleType
import pytest

from app import providers
from app.config import Settings


MODES = [
    ("ollama", "llama_index.llms.ollama", "Ollama", {},
        {"model": "llama3.2:1b", "base_url": "http://127.0.0.1:11434"}),
    ("openai", "llama_index.llms.openai", "OpenAI",
        {"openai_model": "gpt-test"}, {"model": "gpt-test"}),
    ("azure-openai", "llama_index.llms.azure_openai", "AzureOpenAI",
        {"azure_openai_model": "gpt-test",
         "azure_openai_deployment": "azure-test",
         "azure_openai_endpoint": "https://example.openai.azure.com",
         "azure_openai_api_version": "2024-10-21"},
        {"model": "gpt-test", "deployment_name": "azure-test"}),
    ("anthropic", "llama_index.llms.anthropic", "Anthropic",
        {"anthropic_model": "claude-test"}, {"model": "claude-test"}),
    ("bedrock", "llama_index.llms.bedrock_converse", "BedrockConverse",
        {"bedrock_model_id": "amazon.test", "aws_region": "eu-west-1"},
        {"model": "amazon.test", "region_name": "eu-west-1"}),
]


def _fake_sdk(monkeypatch, module, cls):
    seen = {"constructed": 0}
    sdk = ModuleType(module)
    def factory(**kwargs):
        seen["constructed"] += 1
        seen["kwargs"] = kwargs
        return object()
    setattr(sdk, cls, factory)
    monkeypatch.setitem(sys.modules, module, sdk)
    return seen


@pytest.mark.parametrize("name,module,cls,settings,expected", MODES)
def test_explicit_provider_uses_correct_native_llamaindex_class(
        monkeypatch, name, module, cls, settings, expected):
    seen = _fake_sdk(monkeypatch, module, cls)
    instance = providers.create_llm(Settings(provider=name, **settings))
    assert instance is not None
    assert seen["constructed"] == 1
    assert all(seen["kwargs"].get(key) == value for key, value in expected.items())
    assert not any("key" in key.lower() for key in seen["kwargs"])


@pytest.mark.parametrize("name,module,cls,settings,_", MODES[1:])
def test_missing_integration_does_not_leak_installation_details(
        monkeypatch, name, module, cls, settings, _):
    monkeypatch.setitem(sys.modules, module, None)
    with pytest.raises(providers.ProviderError, match="not installed"):
        providers.create_llm(Settings(provider=name, **settings))


@pytest.mark.parametrize("name,module,cls,fields", [
    ("openai", "llama_index.llms.openai", "OpenAI", {}),
    ("azure-openai", "llama_index.llms.azure_openai", "AzureOpenAI",
        {"azure_openai_model": "test"}),
    ("anthropic", "llama_index.llms.anthropic", "Anthropic", {}),
    ("bedrock", "llama_index.llms.bedrock_converse", "BedrockConverse", {}),
])
def test_missing_model_config_fails_closed(monkeypatch, name, module, cls, fields):
    _fake_sdk(monkeypatch, module, cls)
    with pytest.raises(providers.ProviderError, match="Missing required"):
        providers.create_llm(Settings(provider=name, **fields))
