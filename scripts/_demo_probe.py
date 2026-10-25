"""Isolated generated-app consumer proving M1/M5/M6 interoperation.

Invoked exclusively by run_demo.py from a temporary generated project.
"""
from __future__ import annotations

import json

from fastapi.testclient import TestClient

from aet_provider import (
    GenerateRequest,
    LegacyTextAdapter,
    MockProvider,
    OllamaProvider,
    assert_provider_contract,
)
from aet_quality import (
    ToolTrace,
    assert_json_serializable,
    assert_only_tools,
    assert_output_contract,
    assert_tool_called,
    assert_tool_outcome,
    assert_tool_sequence,
)
from app import workflow
from app.config import Settings
from app.main import app
from app.providers import get_provider


def verify() -> dict:
    checks: list[str] = []

    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    checks.append("generated FastAPI health endpoint")

    trace = ToolTrace()
    original = workflow.get_order_status

    def recorded_order_lookup(order_id: str) -> str:
        return trace.invoke("get_order_status", original, order_id=order_id)

    workflow.get_order_status = recorded_order_lookup

    response = client.post("/invoke", json={"question": "order status ORD-1001"})
    assert response.status_code == 200
    known = response.json()
    assert_output_contract(known, {"answer": str, "tool_used": (str, type(None))}, allow_extra=False)
    assert_json_serializable(known)
    assert known == {
        "answer": "Demo order ORD-1001 status: shipped.",
        "tool_used": "get_order_status",
    }
    assert_tool_called(trace, "get_order_status", arguments={"order_id": "ORD-1001"})
    assert_tool_sequence(trace, ["get_order_status"])
    assert_only_tools(trace, {"get_order_status"})
    assert_tool_outcome(trace, "get_order_status", succeeded=True)
    checks.append("quality trace for known synthetic tool execution")

    trace.clear()
    missing = client.post("/invoke", json={"question": "order status ORD-9999"})
    assert missing.status_code == 200
    assert missing.json()["answer"] == "Demo order ORD-9999 was not found."
    assert_tool_called(trace, "get_order_status", arguments={"order_id": "ORD-9999"})
    checks.append("unknown synthetic order behavior")

    trace.clear()
    plain = client.post("/invoke", json={"question": "hello"})
    assert plain.status_code == 200
    assert plain.json() == {"answer": "Mock response to: hello", "tool_used": None}
    assert_tool_called(trace, "get_order_status", times=0)
    checks.append("mock text response without tool invocation")

    invalid = client.post("/invoke", json={"question": ""})
    assert invalid.status_code == 422
    checks.append("generated API input validation")

    mock = MockProvider()
    assert_provider_contract(mock, expected_provider="mock")
    assert mock.generate(GenerateRequest("hello")).text == "Mock response to: hello"
    checks.append("independent typed mock contract")

    existing = get_provider(Settings(provider="mock"))
    portable = LegacyTextAdapter(existing, name="generated-mock", model="generated-v0")
    assert_provider_contract(portable, expected_provider="generated-mock")
    checks.append("legacy generated provider compatibility bridge")

    seen: list[dict] = []

    def fake_local_transport(request, timeout):
        data = json.loads(request.data.decode("utf-8"))
        seen.append(data)
        assert request.full_url == "http://127.0.0.1:11434/api/generate"
        assert data["stream"] is False
        return b'{"response":"synthetic local model response"}'

    local = OllamaProvider(model="fixture-model:1b", transport=fake_local_transport)
    assert_provider_contract(local, expected_provider="ollama")
    assert len(seen) == 1
    assert seen[0]["prompt"] == "portable contract probe"
    checks.append("fake local Ollama transport without a model or network")

    return {
        "status": "passed",
        "checks": checks,
        "count": len(checks),
        "components": ["aet-scaffolder", "aet-agent-quality", "aet-provider-contract"],
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
