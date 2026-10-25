"""Run Olist-style order requests through actual generated FastAPI/LangGraph app.

Used by evaluate_olist.py in a temporary directory. Only prints aggregates.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import time
from pathlib import Path

from fastapi.testclient import TestClient

from aet_quality import (
    ToolTrace, assert_json_serializable, assert_only_tools,
    assert_output_contract, assert_tool_called, assert_tool_outcome,
    assert_tool_sequence,
)
from app import workflow
from app.main import app


def _stats(values: list[float]) -> dict:
    ordered = sorted(values)
    return {
        "median_ms": round(statistics.median(ordered), 3),
        "p95_nearest_rank_ms": round(ordered[math.ceil(0.95 * len(ordered)) - 1], 3),
        "max_ms": round(ordered[-1], 3),
    }


def verify(orders: dict[str, str], queries: int) -> dict:
    if not orders or not 1 <= queries <= len(orders):
        raise ValueError("No orders or invalid query count")
    trace = ToolTrace()
    workflow._ORDER_COMMAND = re.compile(r"\s*order\s+status\s+([0-9a-f]{32})\s*", re.I)

    def lookup(order_id: str) -> str:
        def from_records(order_id: str) -> str:
            status = orders.get(order_id)
            if status is None:
                return f"Demo order {order_id} was not found."
            return f"Demo order {order_id} status: {status}."

        return trace.invoke("get_order_status", from_records, order_id=order_id)

    workflow.get_order_status = lookup
    client = TestClient(app)
    measured_ms = []
    correct = 0
    selected = sorted(orders)[:queries]
    for idx, oid in enumerate(selected):
        # Verify route is case-insensitive, including hex letter case.
        typed_id = oid.lower() if idx % 2 else oid
        trace.clear()
        begin = time.perf_counter_ns()
        response = client.post("/invoke", json={"question": f"order status {typed_id}"})
        duration = (time.perf_counter_ns() - begin) / 1_000_000
        measured_ms.append(duration)
        expected = {
            "answer": f"Demo order {oid} status: {orders[oid]}.",
            "tool_used": "get_order_status",
        }
        if response.status_code == 200 and response.json() == expected:
            correct += 1
        assert_output_contract(response.json(), {"answer": str, "tool_used": (str, type(None))},
                               allow_extra=False)
        assert_json_serializable(response.json())
        assert_tool_called(trace, "get_order_status", arguments={"order_id": oid})
        assert_tool_sequence(trace, ["get_order_status"])
        assert_tool_outcome(trace, "get_order_status", succeeded=True)
        assert_only_tools(trace, {"get_order_status"})

    negative_id = next(f"{n:032X}" for n in range(10000) if f"{n:032X}" not in orders)
    trace.clear()
    missing = client.post("/invoke", json={"question": f"order status {negative_id}"})
    negative_ok = (missing.status_code == 200 and missing.json() == {
        "answer": f"Demo order {negative_id} was not found.",
        "tool_used": "get_order_status",
    })
    assert_tool_called(trace, "get_order_status", arguments={"order_id": negative_id})
    trace.clear()
    malformed = client.post("/invoke", json={"question": "order status INVALID"})
    malformed_ok = malformed.status_code == 200 and malformed.json() == {
        "answer": "Mock response to: order status INVALID", "tool_used": None,
    }
    assert_tool_called(trace, "get_order_status", times=0)
    if correct != len(selected) or not negative_ok or not malformed_ok:
        raise AssertionError("At least one order-status output differed from expected")

    return {
        "status": "passed",
        "known_tested": len(selected),
        "known_correct": correct,
        "known_accuracy_pct": round(100 * correct / len(selected), 2),
        "unknown_tested": 1,
        "unknown_correct": int(negative_ok),
        "malformed_request_rejected_from_tool": malformed_ok,
        "request_latency": _stats(measured_ms),
        "latency_scope": "in-process FastAPI TestClient + LangGraph + local dictionary tool (not network latency)",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", required=True)
    parser.add_argument("--queries", type=int, required=True)
    args = parser.parse_args()
    mapping = json.loads(Path(args.records).read_text(encoding="utf-8"))
    print(json.dumps(verify(mapping, args.queries), allow_nan=False))


if __name__ == "__main__":
    main()
