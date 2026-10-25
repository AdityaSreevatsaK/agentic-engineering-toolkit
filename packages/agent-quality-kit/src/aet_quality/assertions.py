"""Small, deterministic, actionable assertions for reusable agent tests."""
from __future__ import annotations

import json
from collections.abc import Collection, Mapping, Sequence
from typing import Any

from .trace import ToolCall, ToolTrace


def _events(trace: ToolTrace | Sequence[ToolCall]) -> tuple[ToolCall, ...]:
    if isinstance(trace, ToolTrace):
        return trace.calls
    if isinstance(trace, (str, bytes)) or not isinstance(trace, Sequence):
        raise TypeError("expected ToolTrace or a sequence of ToolCall events")
    if not all(isinstance(event, ToolCall) for event in trace):
        raise TypeError("each event must be ToolCall")
    return tuple(trace)


def _count(times: int) -> None:
    if type(times) is not int or times < 0:
        raise ValueError("times must be a non-negative integer")


def assert_tool_called(
    trace: ToolTrace | Sequence[ToolCall],
    name: str,
    *,
    times: int = 1,
    arguments: Mapping[str, Any] | None = None,
) -> None:
    """Assert exact invocation count, optionally including exact argument equality."""
    _count(times)
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a nonempty string")
    if arguments is not None and not isinstance(arguments, Mapping):
        raise TypeError("arguments must be a mapping")
    matches = [
        event for event in _events(trace)
        if event.name == name and (arguments is None or event.arguments == dict(arguments))
    ]
    assert len(matches) == times, (
        f"Expected {name!r} to be called {times} time(s), but found {len(matches)}."
    )


def assert_tool_outcome(
    trace: ToolTrace | Sequence[ToolCall], name: str, *, succeeded: bool, times: int = 1
) -> None:
    """Assert count of successful or unsuccessful tool executions."""
    _count(times)
    if type(succeeded) is not bool:
        raise TypeError("succeeded must be boolean")
    matches = [e for e in _events(trace) if e.name == name and e.succeeded is succeeded]
    assert len(matches) == times, (
        f"Expected {times} {name!r} tool call(s) with succeeded={succeeded}; found {len(matches)}."
    )


def assert_tool_sequence(
    trace: ToolTrace | Sequence[ToolCall], expected: Sequence[str], *, exact: bool = True
) -> None:
    """Compare call order; exact=False accepts an ordered subsequence."""
    if isinstance(expected, (str, bytes)) or not isinstance(expected, Sequence):
        raise TypeError("expected names must be a sequence of strings")
    if any(not isinstance(item, str) or not item for item in expected):
        raise ValueError("every expected tool name must be a nonempty string")
    actual = [event.name for event in _events(trace)]
    expected_names = list(expected)
    if exact:
        assert actual == expected_names, (
            f"Expected tool sequence {expected_names!r}; observed {actual!r}."
        )
    else:
        remaining = iter(actual)
        assert all(any(name == wanted for name in remaining) for wanted in expected_names), (
            f"Expected ordered subsequence {expected_names!r}; observed {actual!r}."
        )


def assert_only_tools(trace: ToolTrace | Sequence[ToolCall], allowed: Collection[str]) -> None:
    """Assert no unapproved tool names were observed."""
    if isinstance(allowed, (str, bytes)):
        raise TypeError("allowed must be a collection of tool names, not a string")
    approved = set(allowed)
    if any(not isinstance(name, str) for name in approved):
        raise TypeError("allowed tool names must be strings")
    unapproved = sorted({event.name for event in _events(trace)} - approved)
    assert not unapproved, f"Unexpected tool names: {unapproved!r}"


def assert_output_contract(
    output: Mapping[str, Any],
    required: Mapping[str, type | tuple[type, ...]],
    *,
    allow_extra: bool = True,
) -> None:
    """Validate top-level output fields and their types without external libraries.

    This is intentionally a lightweight contract, not a full JSON Schema validator.
    Python bool is not silently accepted as an int or float.
    """
    if not isinstance(output, Mapping) or not isinstance(required, Mapping):
        raise TypeError("output and required fields must be mappings")
    if type(allow_extra) is not bool:
        raise TypeError("allow_extra must be boolean")
    for key, accepted in required.items():
        if not isinstance(key, str):
            raise TypeError("required field names must be strings")
        candidates = accepted if isinstance(accepted, tuple) else (accepted,)
        if not candidates or any(not isinstance(t, type) for t in candidates):
            raise TypeError("expected field types must be types or nonempty tuples of types")
        assert key in output, f"Missing required output field: {key!r}"
        value = output[key]
        ok = any(
            type(value) is typ if typ in (str, int, float, bool, dict, list, type(None))
            else isinstance(value, typ)
            for typ in candidates
        )
        assert ok, f"Output field {key!r} has type {type(value).__name__}; contract not satisfied."
    if not allow_extra:
        extras = sorted(set(output) - set(required), key=str)
        assert not extras, f"Unexpected output fields: {extras!r}"


def assert_json_serializable(value: Any) -> None:
    """Require strict RFC-compliant JSON, rejecting NaN and Infinity."""
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError, OverflowError) as exc:
        raise AssertionError("Output cannot be encoded as strict JSON") from exc
