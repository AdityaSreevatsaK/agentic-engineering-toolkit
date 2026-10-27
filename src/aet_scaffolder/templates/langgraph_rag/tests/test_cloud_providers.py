"""M16: cloud provider SDK wiring is verified entirely with injected offline fakes."""
import sys
from types import ModuleType, SimpleNamespace

import pytest
from pydantic import ValidationError

from app import providers
from app.config import Settings


MODES = [
    ("openai", "langchain_openai", "ChatOpenAI",
     {"openai_model": "gpt-test"}, {"model": "gpt-test"}),
    ("azure-openai", "langchain_openai", "AzureChatOpenAI",
     {"azure_openai_deployment": "deployment-test",
      "azure_openai_endpoint": "https://unit-test.openai.azure.com/",
      "azure_openai_api_version": "2024-10-21"},
     {"azure_deployment": "deployment-test",
      "azure_endpoint": "https://unit-test.openai.azure.com",
      "api_version": "2024-10-21"}),
    ("anthropic", "langchain_anthropic", "ChatAnthropic",
     {"anthropic_model": "claude-test"}, {"model": "claude-test"}),
    ("bedrock", "langchain_aws", "ChatBedrock",
     {"bedrock_model_id": "amazon.unit-test", "aws_region": "us-west-2"},
     {"model_id": "amazon.unit-test", "region_name": "us-west-2"}),
]


def _fake_sdk(monkeypatch, module, cls_name, *, result="Cloud response", failure=None):
    observed = {"calls": 0}
    fake = ModuleType(module)

    class OfflineChatModel:
        def __init__(self, **kwargs):
            observed["kwargs"] = kwargs

        def invoke(self, prompt):
            observed["calls"] += 1
            observed["prompt"] = prompt
            if failure:
                raise RuntimeError(failure)
            return SimpleNamespace(content=result)

    setattr(fake, cls_name, OfflineChatModel)
    monkeypatch.setitem(sys.modules, module, fake)
    return observed


@pytest.mark.parametrize("name,module,cls_name,fields,expected", MODES)
def test_framework_native_sdk_configuration_is_offline(
        monkeypatch, name, module, cls_name, fields, expected):
    seen = _fake_sdk(monkeypatch, module, cls_name)
    cfg = Settings(provider=name, model_timeout_seconds=27,
                   model_max_retries=0, **fields)
    text = providers.get_provider(cfg).generate("sample prompt")
    assert text == "Cloud response"
    assert seen["calls"] == 1
    assert seen["prompt"] == "sample prompt"
    assert all(seen["kwargs"][key] == value for key, value in expected.items())
    # SDKs read native credentials securely; the scaffold never embeds them.
    assert not any("key" in key.lower() or "password" in key.lower()
                   for key in seen["kwargs"])
    if name != "bedrock":
        assert seen["kwargs"]["timeout"] == 27
        assert seen["kwargs"]["max_retries"] == 0


@pytest.mark.parametrize("name,module,cls_name,fields,_", MODES)
def test_cloud_sdk_failures_do_not_expose_provider_details(
        monkeypatch, name, module, cls_name, fields, _):
    _fake_sdk(monkeypatch, module, cls_name, failure="secret-token-and-URL")
    service = providers.get_provider(Settings(provider=name, **fields))
    with pytest.raises(providers.ProviderError) as err:
        service.generate("test")
    assert "secret-token-and-URL" not in str(err.value)


@pytest.mark.parametrize("name,module,cls_name,fields,_", MODES)
def test_uninstalled_optional_sdk_is_safely_reported(
        monkeypatch, name, module, cls_name, fields, _):
    monkeypatch.setitem(sys.modules, module, None)
    with pytest.raises(providers.ProviderError, match="not installed"):
        providers.get_provider(Settings(provider=name, **fields))


@pytest.mark.parametrize("name,fields", [
    ("openai", {}),
    ("azure-openai", {"azure_openai_endpoint": "https://unit-test.openai.azure.com"}),
    ("anthropic", {}),
    ("bedrock", {}),
])
def test_missing_cloud_model_config_fails_closed(monkeypatch, name, fields):
    module = "langchain_openai" if name in {"openai", "azure-openai"} else (
        "langchain_anthropic" if name == "anthropic" else "langchain_aws"
    )
    cls_name = {
        "openai": "ChatOpenAI", "azure-openai": "AzureChatOpenAI",
        "anthropic": "ChatAnthropic", "bedrock": "ChatBedrock",
    }[name]
    _fake_sdk(monkeypatch, module, cls_name)
    with pytest.raises(providers.ProviderError, match="Missing required"):
        providers.get_provider(Settings(provider=name, **fields))


@pytest.mark.parametrize("unsafe", [
    "http://example.openai.azure.com", "https://user:secret@host.example",
    "https://host.example/extra", "https://host.example/?key=secret",
])
def test_azure_endpoint_must_be_bare_https(unsafe):
    with pytest.raises(ValidationError):
        Settings(azure_openai_endpoint=unsafe)


def test_anthropic_multiblock_text_response(monkeypatch):
    _fake_sdk(monkeypatch, "langchain_anthropic", "ChatAnthropic", result=[
        {"type": "thinking", "thinking": "hidden"},
        {"type": "text", "text": "Grounded "},
        {"type": "text", "text": "answer"},
    ])
    service = providers.get_provider(Settings(provider="anthropic", anthropic_model="test"))
    assert service.generate("hello") == "Grounded answer"


@pytest.mark.parametrize(
    "bad", ["", [], [1], "a" * 1_000_001],
    ids=["empty-string", "empty-blocks", "invalid-block", "oversized-text"],
)
def test_invalid_cloud_text_is_rejected(monkeypatch, bad):
    _fake_sdk(monkeypatch, "langchain_openai", "ChatOpenAI", result=bad)
    service = providers.get_provider(Settings(provider="openai", openai_model="test"))
    with pytest.raises(providers.ProviderError, match="empty or oversized"):
        service.generate("hello")


def test_bedrock_uses_sdk_region_environment_fallback(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "eu-west-1")
    seen = _fake_sdk(monkeypatch, "langchain_aws", "ChatBedrock")
    providers.get_provider(Settings(provider="bedrock", bedrock_model_id="amazon.test"))
    assert seen["kwargs"]["region_name"] == "eu-west-1"


def test_grounded_question_reaches_cloud_with_evidence(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.setenv("AET_PROVIDER", "openai")
    monkeypatch.setenv("AET_OPENAI_MODEL", "test-model")
    seen = _fake_sdk(monkeypatch, "langchain_openai", "ChatOpenAI")
    response = TestClient(app).post("/ask", json={"question": "What is the return policy?"})
    assert response.status_code == 200
    assert response.json()["answer"] == "Cloud response"
    assert "returns" in response.json()["source_ids"]
    assert "[returns]" in seen["prompt"]
    assert "30 days" in seen["prompt"]
    assert seen["calls"] == 1


def test_no_retrieval_hit_never_initialises_cloud(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.setenv("AET_PROVIDER", "openai")
    monkeypatch.setenv("AET_OPENAI_MODEL", "test-model")
    seen = _fake_sdk(monkeypatch, "langchain_openai", "ChatOpenAI")
    response = TestClient(app).post("/ask", json={"question": "astrophysics nebula"})
    assert response.status_code == 200
    assert response.json()["source_ids"] == []
    assert "No relevant passages" in response.json()["answer"]
    assert seen["calls"] == 0
    assert "kwargs" not in seen


def test_cloud_api_error_is_sanitised(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.setenv("AET_PROVIDER", "openai")
    monkeypatch.setenv("AET_OPENAI_MODEL", "test-model")
    _fake_sdk(monkeypatch, "langchain_openai", "ChatOpenAI", failure="highly-sensitive-sdk-error")
    response = TestClient(app).post("/ask", json={"question": "return policy"})
    assert response.status_code == 503
    assert "highly-sensitive-sdk-error" not in response.text
