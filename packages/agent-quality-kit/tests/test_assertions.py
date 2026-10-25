"""Assertion primitives do not require an agent SDK, cloud, or model."""
import math
import pytest

from aet_quality import (
    ToolTrace,
    assert_json_serializable,
    assert_only_tools,
    assert_output_contract,
    assert_tool_called,
    assert_tool_outcome,
    assert_tool_sequence,
)


def make_trace():
    trace = ToolTrace()
    trace.record("retrieve", {"query": "synthetic"})
    trace.record("format", {"format": "json"})
    trace.record("retrieve", {"query": "synthetic"}, succeeded=False, error_type="RuntimeError")
    return trace


def test_exact_tool_call_counts_and_arguments():
    trace = make_trace()
    assert_tool_called(trace, "retrieve", times=2)
    assert_tool_called(trace, "retrieve", arguments={"query": "synthetic"}, times=2)
    assert_tool_called(trace, "missing", times=0)
    with pytest.raises(AssertionError, match="Expected"):
        assert_tool_called(trace, "retrieve", times=1)


def test_tool_call_exact_argument_matching():
    trace = make_trace()
    assert_tool_called(trace, "retrieve", arguments={"query": "different"}, times=0)
    with pytest.raises(AssertionError):
        assert_tool_called(trace, "retrieve", arguments={}, times=1)


def test_tool_success_and_failure():
    trace = make_trace()
    assert_tool_outcome(trace, "retrieve", succeeded=True)
    assert_tool_outcome(trace, "retrieve", succeeded=False)
    with pytest.raises(AssertionError):
        assert_tool_outcome(trace, "format", succeeded=False)


def test_sequence_and_subsequence():
    trace = make_trace()
    assert_tool_sequence(trace, ["retrieve", "format", "retrieve"])
    assert_tool_sequence(trace, ["retrieve", "retrieve"], exact=False)
    assert_tool_sequence(trace, [], exact=False)
    with pytest.raises(AssertionError):
        assert_tool_sequence(trace, ["format", "retrieve", "format"], exact=False)
    with pytest.raises(AssertionError):
        assert_tool_sequence(trace, ["format", "retrieve"])


def test_tool_allowlist():
    trace = make_trace()
    assert_only_tools(trace, {"retrieve", "format"})
    with pytest.raises(AssertionError, match="Unexpected"):
        assert_only_tools(trace, {"format"})


def test_output_contract_optional_and_extra_fields():
    output = {"answer": "ok", "tool_used": None, "metadata": {"synthetic": True}}
    assert_output_contract(output, {"answer": str, "tool_used": (str, type(None))})
    with pytest.raises(AssertionError, match="Unexpected"):
        assert_output_contract(output, {"answer": str}, allow_extra=False)


def test_output_contract_missing_and_wrong_type():
    with pytest.raises(AssertionError, match="Missing"):
        assert_output_contract({}, {"answer": str})
    with pytest.raises(AssertionError, match="type"):
        assert_output_contract({"answer": False}, {"answer": str})
    with pytest.raises(AssertionError):
        assert_output_contract({"count": True}, {"count": int})


def test_output_contract_rejects_invalid_type_spec():
    with pytest.raises(TypeError):
        assert_output_contract({"answer": "yes"}, {"answer": "str"})
    with pytest.raises(TypeError):
        assert_output_contract([], {"answer": str})


def test_output_json_validation():
    assert_json_serializable({"answer": "ok", "success": True})
    with pytest.raises(AssertionError, match="strict JSON"):
        assert_json_serializable({"value": math.nan})
    with pytest.raises(AssertionError):
        assert_json_serializable({"n": object()})


def test_invalid_expected_count_rejected():
    with pytest.raises(ValueError):
        assert_tool_called(make_trace(), "retrieve", times=-1)
    with pytest.raises(ValueError):
        assert_tool_outcome(make_trace(), "retrieve", times=True, succeeded=True)
