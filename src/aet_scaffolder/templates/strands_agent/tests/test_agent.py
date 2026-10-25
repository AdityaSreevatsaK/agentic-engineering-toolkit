"""Exercise the actual Strands SDK agent loop without external services."""
import pytest

from app import agent as agent_module
from app.config import Settings
from app.offline_model import OfflineModel


def test_tool_is_invoked_by_strands_offline_model():
    answer, used_tool = agent_module.run_agent(
        "order status ORD-1001", Settings(provider="mock")
    )
    assert used_tool is True
    assert "ORD-1001" in answer
    assert "shipped" in answer.lower()


def test_second_sample_and_unknown_order():
    for order, expected in (("ORD-1002", "processing"), ("ORD-9999", "not found")):
        answer, used = agent_module.run_agent(
            "order status " + order, Settings(provider="mock")
        )
        assert used is True
        assert expected in answer.lower()


def test_plain_question_does_not_invoke_tool():
    answer, used = agent_module.run_agent("hello", Settings(provider="mock"))
    assert used is False
    assert "offline strands demo" in answer.lower()


def test_mock_never_constructs_bedrock(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("AWS must not be touched by the offline mode")
    monkeypatch.setattr(agent_module, "BedrockModel", forbidden)
    answer, used = agent_module.run_agent(
        "order status ORD-1003", Settings(provider="mock")
    )
    assert used is True
    assert "delivered" in answer.lower()


def test_bedrock_provider_constructs_correct_sdk_model_with_injected_stub(monkeypatch):
    seen = {}

    def fake_bedrock(**kwargs):
        seen.update(kwargs)
        return OfflineModel()

    monkeypatch.setattr(agent_module, "BedrockModel", fake_bedrock)
    settings = Settings(
        provider="bedrock",
        aws_region="eu-west-1",
        bedrock_model_id="eu.amazon.nova-lite-v1:0",
    )
    result, used = agent_module.run_agent("order status ORD-1001", settings)
    assert seen == {
        "model_id": "eu.amazon.nova-lite-v1:0",
        "region_name": "eu-west-1",
        "streaming": False,
    }
    assert used is True
    assert "shipped" in result.lower()


def test_invalid_region_and_model_id_rejected():
    with pytest.raises(ValueError):
        Settings(provider="bedrock", aws_region="a malicious region")
    with pytest.raises(ValueError):
        Settings(provider="bedrock", bedrock_model_id="bad model\n")
