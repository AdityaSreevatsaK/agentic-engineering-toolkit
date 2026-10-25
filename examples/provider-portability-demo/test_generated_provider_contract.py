"""Run against a freshly generated app with only synthetic data.

The standalone contract library imports neither the AET scaffolder nor LangGraph.
"""
from aet_provider import (
    GenerateRequest,
    LegacyTextAdapter,
    assert_provider_contract,
)
from app.config import Settings
from app.providers import get_provider


def test_current_generated_mock_implements_portability_contract():
    existing = get_provider(Settings(provider="mock"))
    portable = LegacyTextAdapter(existing, name="generated-mock", model="generated-v0")
    assert_provider_contract(portable, expected_provider="generated-mock")
    assert portable.generate(GenerateRequest("hello")).text == "Mock response to: hello"
