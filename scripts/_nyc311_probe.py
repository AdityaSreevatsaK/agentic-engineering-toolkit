"""Run a real generated FastAPI/LangGraph app with public request IDs in memory.

Print only aggregate output, never individual NYC 311 records.
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
    ToolTrace, assert_tool_called, assert_tool_outcome,
    assert_tool_sequence, assert_only_tools, assert_output_contract,
)
from app import workflow
from app.main import app


def _stats(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    return {
        "median_ms": round(statistics.median(ordered), 3),
        "p95_nearest_rank_ms": round(ordered[math.ceil(.95 * len(ordered)) - 1], 3),
        "max_ms": round(ordered[-1], 3),
    }


def verify(records: dict[str, str], queries: int) -> dict:
    if not records or not 1 <= queries <= len(records):
        raise ValueError("Invalid record/query count")

    # Only the generated *temporary* test project's graph is patched.
    # The original scaffolder's demo tool remains completely unchanged.
    workflow._ORDER_COMMAND = re.compile(
        r"\s*service\s+request\s+status\s+([0-9]{6,12})\s*", re.IGNORECASE
    )
    trace = ToolTrace()

    def lookup(service_id: str) -> str:
        def local_lookup(order_id: str) -> str:
            status = records.get(order_id)
            return (f"Demo request {order_id} status: {status}."
                    if status is not None else f"Demo request {order_id} was not found.")
        return trace.invoke("get_order_status", local_lookup, order_id=service_id)

    workflow.get_order_status = lookup
    client = TestClient(app)
    latencies = []
    accepted = 0
    selected = sorted(records)[:queries]
    for service_id in selected:
        trace.clear()
        started = time.perf_counter_ns()
        response = client.post("/invoke", json={"question": f"service request status {service_id}"})
        latencies.append((time.perf_counter_ns() - started) / 1_000_000)
        valid = response.status_code == 200 and response.json() == {
            "answer": f"Demo request {service_id} status: {records[service_id]}.",
            "tool_used": "get_order_status",
        }
        accepted += int(valid)
        assert_output_contract(response.json(), {
            "answer": str, "tool_used": (str, type(None))
        }, allow_extra=False)
        assert_tool_called(trace, "get_order_status", arguments={"order_id": service_id}, times=1)
        assert_tool_outcome(trace, "get_order_status", succeeded=True, times=1)
        assert_tool_sequence(trace, ["get_order_status"])
        assert_only_tools(trace, {"get_order_status"})

    missing_id = next(f"{n:08d}" for n in range(1000) if f"{n:08d}" not in records)
    trace.clear()
    unknown = client.post("/invoke", json={"question": f"service request status {missing_id}"})
    correct_missing = (unknown.status_code == 200 and unknown.json() == {
        "answer": f"Demo request {missing_id} was not found.",
        "tool_used": "get_order_status",
    })
    assert_tool_called(trace, "get_order_status", times=1)
    trace.clear()
    malformed = client.post("/invoke", json={"question": "service request status invalid"})
    correct_malformed = (malformed.status_code == 200 and malformed.json() == {
        "answer": "Mock response to: service request status invalid",
        "tool_used": None,
    })
    assert_tool_called(trace, "get_order_status", times=0)
    if accepted != len(selected) or not correct_missing or not correct_malformed:
        raise AssertionError("A local status lookup assertion was not satisfied")
    return {
        "status": "passed",
        "known_tested": len(selected),
        "known_correct": accepted,
        "known_accuracy_pct": round(100 * accepted / len(selected), 2),
        "unknown_tested": 1,
        "unknown_correct": int(correct_missing),
        "malformed_request_skipped_tool": correct_malformed,
        "in_process_latency": _stats(latencies),
        "latency_scope": "FastAPI TestClient + LangGraph + in-memory lookup; not network or model inference",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--queries", type=int, required=True)
    args = parser.parse_args()
    records = json.loads(Path(args.input).read_text(encoding="utf-8"))
    print(json.dumps(verify(records, args.queries), allow_nan=False))


if __name__ == "__main__":
    main()
