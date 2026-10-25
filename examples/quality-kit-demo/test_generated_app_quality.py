"""Opt-in integration tests against a freshly generated agent project.

CI installs the generated mock app and the standalone Quality Kit first.
Quality Kit does not import the scaffolder or LangGraph.
"""
from fastapi.testclient import TestClient

from aet_quality import (
    assert_json_serializable,
    assert_only_tools,
    assert_output_contract,
    assert_tool_called,
    assert_tool_sequence,
)

from app import workflow
from app.main import app


def test_real_generated_workflow_calls_synthetic_tool(monkeypatch, agent_trace):
    original = workflow.get_order_status

    def spy(order_id):
        return agent_trace.invoke("get_order_status", original, order_id=order_id)

    monkeypatch.setattr(workflow, "get_order_status", spy)
    response = TestClient(app).post("/invoke", json={"question": "order status ORD-1001"})
    assert response.status_code == 200
    body = response.json()
    assert_output_contract(body, {"answer": str, "tool_used": (str, type(None))}, allow_extra=False)
    assert_json_serializable(body)
    assert_tool_called(agent_trace, "get_order_status", arguments={"order_id": "ORD-1001"})
    assert_tool_sequence(agent_trace, ["get_order_status"])
    assert_only_tools(agent_trace, {"get_order_status"})
    assert body["answer"] == "Demo order ORD-1001 status: shipped."


def test_fallback_skips_order_tool(monkeypatch, agent_trace):
    original = workflow.get_order_status

    def spy(order_id):
        return agent_trace.invoke("get_order_status", original, order_id=order_id)

    monkeypatch.setattr(workflow, "get_order_status", spy)
    monkeypatch.setenv("AET_PROVIDER", "mock")
    response = TestClient(app).post("/invoke", json={"question": "hello"})
    assert response.status_code == 200
    assert_tool_called(agent_trace, "get_order_status", times=0)
    assert_output_contract(
        response.json(), {"answer": str, "tool_used": (str, type(None))}, allow_extra=False
    )
