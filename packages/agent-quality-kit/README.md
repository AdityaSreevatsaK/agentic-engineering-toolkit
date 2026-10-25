# AET Agent Quality Kit

An **independently installable**, deterministic Python testing package for tool-calling applications. It has no runtime dependencies on LangGraph, Strands, Ollama, OpenAI, cloud SDKs, or the AET scaffolder.

**M5 scope:** tool-call recording, success/failure assertions, exact/ordered tool selection, allowlist checks, top-level output-type contracts, JSON serializability, and an opt-in pytest fixture. It does not score model quality or replace enterprise evaluation platforms.

## Install locally from this private monorepo

```powershell
python -m pip install -e "./packages/agent-quality-kit[dev]"
python -m pytest packages/agent-quality-kit/tests -q
```

When working from inside `packages/agent-quality-kit`, run `python -m pip install -e ".[dev]"` and `python -m pytest`.

## Usage

```python
from aet_quality import (
    ToolTrace, assert_tool_called, assert_tool_sequence,
    assert_only_tools, assert_output_contract,
)

trace = ToolTrace()
result = trace.invoke("lookup", lambda order_id: {"status": "shipped"}, order_id="ORD-1001")
assert_tool_called(trace, "lookup", arguments={"order_id": "ORD-1001"})
assert_tool_sequence(trace, ["lookup"])
assert_only_tools(trace, {"lookup"})
assert_output_contract(result, {"status": str}, allow_extra=False)
```

In pytest, use the auto-registered `agent_trace` fixture to obtain an independent trace for each test. A complete integration example is in `examples/quality-kit-demo/test_generated_app_quality.py` and is exercised in private CI against a freshly generated AET project.

## Design and security boundaries

- Tool calls are captured **only when explicitly recorded/invoked** through `ToolTrace`. No global monkeypatching, background network calls, automatic provider instrumentation, telemetry, or client data collection.
- Argument snapshots use `deepcopy` and may be retained in memory. Use only synthetic or approved test data; do not record secrets, tokens, or client information.
- Core imports do not require pytest. The pytest plugin imports pytest when discovered during test execution.
- `assert_output_contract` checks top-level field types. It is intentionally not a complete JSON Schema validator.
- This package does not prove LLM safety, reliability, security, or production readiness.
