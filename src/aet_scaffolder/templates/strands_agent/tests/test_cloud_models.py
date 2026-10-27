"""M17 native Strands cloud integrations: all network paths replaced with test doubles."""
import sys
from types import ModuleType

import pytest

from app import agent as agent_module
from app import cloud_models
from app.config import Settings
from app.offline_model import OfflineModel


def _fake_module(monkeypatch, name: str, **attrs):
    module = ModuleType(name)
    for attr, value in attrs.items():
        setattr(module, attr, value)
    monkeypatch.setitem(sys.modules, name, module)


def _stub_provider(monkeypatch, kind):
    seen = {"calls": 0}
    def model_factory(**kwargs):
        seen["calls"] += 1
        seen["model_args"] = kwargs
        return OfflineModel()
    if kind in {"openai", "azure-openai"}:
        _fake_module(monkeypatch, "strands.models.openai", OpenAIModel=model_factory)
    if kind == "anthropic":
        _fake_module(monkeypatch, "strands.models.anthropic", AnthropicModel=model_factory)
    if kind == "azure-openai":
        def azure_client(**kwargs):
            seen["client_args"] = kwargs
            return object()
        _fake_module(monkeypatch, "openai", AsyncAzureOpenAI=azure_client)
    return seen


@pytest.mark.parametrize(("kind", "params", "expected"), [
    ("openai", {"openai_model": "gpt-test"}, {"model_id": "gpt-test"}),
    ("anthropic", {"anthropic_model": "claude-test", "anthropic_max_tokens": 512},
     {"model_id": "claude-test", "max_tokens": 512}),
    ("azure-openai", {"azure_openai_deployment": "deployment-test",
      "azure_openai_endpoint": "https://test.openai.azure.com/",
      "azure_openai_api_version": "2024-10-21"}, {"model_id": "deployment-test"}),
])
def test_sdk_native_model_and_real_strands_tool_loop(monkeypatch, kind, params, expected):
    seen = _stub_provider(monkeypatch, kind)
    cfg = Settings(provider=kind, **params)
    answer, used = agent_module.run_agent("order status ORD-1001", cfg)
    assert used is True
    assert "shipped" in answer.lower()
    assert seen["calls"] == 1
    for key, value in expected.items():
        assert seen["model_args"][key] == value
    assert not any("api_key" in key for key in seen["model_args"])
    if kind == "azure-openai":
        assert "client" in seen["model_args"]
        assert seen["client_args"] == {
            "azure_endpoint": "https://test.openai.azure.com",
            "api_version": "2024-10-21",
            "azure_deployment": "deployment-test",
        }


@pytest.mark.parametrize(("kind", "params"), [
    ("openai", {"openai_model": ""}),
    ("anthropic", {"anthropic_model": ""}),
    ("azure-openai", {"azure_openai_endpoint": "",
      "azure_openai_api_version": "2024-10-21",
      "azure_openai_deployment": "deployment-test"}),
])
def test_provider_cannot_be_used_without_required_model_parameters(
        monkeypatch, kind, params):
    _stub_provider(monkeypatch, kind)
    with pytest.raises(ValueError, match="Missing required"):
        cloud_models.create_cloud_model(Settings(provider=kind, **params))


@pytest.mark.parametrize("kind", ["openai", "anthropic", "azure-openai"])
def test_missing_optional_native_dependency_gives_sanitised_error(monkeypatch, kind):
    module = "strands.models.anthropic" if kind == "anthropic" else "strands.models.openai"
    monkeypatch.setitem(sys.modules, module, None)
    if kind == "azure-openai":
        _fake_module(monkeypatch, "openai", AsyncAzureOpenAI=lambda **kw: object())
    params = {
        "openai": {"openai_model": "model"},
        "anthropic": {"anthropic_model": "model"},
        "azure-openai": {"azure_openai_deployment": "deploy",
                         "azure_openai_api_version": "2024-10-21",
                         "azure_openai_endpoint": "https://test.openai.azure.com"},
    }
    with pytest.raises(RuntimeError, match="not installed"):
        cloud_models.create_cloud_model(Settings(provider=kind, **params[kind]))


@pytest.mark.parametrize("unsafe", [
    "http://test.openai.azure.com",
    "https://user:secret@test.openai.azure.com",
    "https://test.openai.azure.com/deployments",
    "https://test.openai.azure.com/?secret=token",
    "https://test.openai.azure.com:8443",
])
def test_unsafe_azure_endpoint_is_rejected(unsafe):
    with pytest.raises(ValueError):
        Settings(provider="azure-openai", azure_openai_endpoint=unsafe)


@pytest.mark.parametrize("kind", ["openai", "anthropic", "azure-openai"])
def test_mock_mode_does_not_initialise_any_cloud_sdk(monkeypatch, kind):
    seen = _stub_provider(monkeypatch, kind)
    result, used = agent_module.run_agent("order status ORD-1001", Settings(provider="mock"))
    assert used is True
    assert "shipped" in result.lower()
    assert seen["calls"] == 0


@pytest.mark.parametrize("kind", ["openai", "anthropic", "azure-openai"])
def test_live_provider_never_returns_raw_error_from_api(monkeypatch, kind):
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.setenv("AET_PROVIDER", kind)
    def private_failure(*args, **kwargs):
        raise RuntimeError("credential-or-private-host-in-SDK-exception")
    monkeypatch.setattr(agent_module, "create_cloud_model", private_failure)
    response = TestClient(app).post("/invoke", json={"question": "hello"})
    assert response.status_code == 503
    assert "credential-or-private-host-in-SDK-exception" not in response.text
