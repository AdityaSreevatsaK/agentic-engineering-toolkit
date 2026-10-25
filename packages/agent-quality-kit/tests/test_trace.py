"""Trace isolation, recording semantics and predictable error behavior."""
import pytest

from aet_quality import ToolCall, ToolTrace


def test_record_detaches_mutable_arguments():
    trace = ToolTrace()
    original = {"nested": {"items": [1]}}
    trace.record("lookup", original)
    original["nested"]["items"].append(2)
    assert trace.calls[0].arguments == {"nested": {"items": [1]}}
    returned = trace.calls[0]
    returned.arguments["nested"]["items"].append(9)
    assert trace.calls[0].arguments == {"nested": {"items": [1]}}


def test_successful_invoke_preserves_result_and_records_tool():
    trace = ToolTrace()
    assert trace.invoke("sum", lambda x, y: x + y, x=2, y=3) == 5
    assert trace.calls == (ToolCall("sum", {"x": 2, "y": 3}),)


def test_failed_invoke_records_error_type_and_reraises():
    trace = ToolTrace()

    def explode(order_id):
        raise KeyError(order_id)

    with pytest.raises(KeyError, match="missing"):
        trace.invoke("lookup", explode, order_id="missing")
    assert trace.calls == (
        ToolCall("lookup", {"order_id": "missing"}, succeeded=False, error_type="KeyError"),
    )


def test_multiple_calls_and_clear():
    trace = ToolTrace()
    trace.record("one")
    trace.record("two", {"id": 7})
    assert [event.name for event in trace.calls] == ["one", "two"]
    trace.clear()
    assert trace.calls == ()


@pytest.mark.parametrize("name", ["", " ", None, 10])
def test_reject_bad_tool_name(name):
    with pytest.raises(ValueError):
        ToolTrace().record(name)


def test_reject_arguments_that_are_not_a_mapping():
    with pytest.raises(TypeError):
        ToolTrace().record("tool", [1, 2])


def test_reject_inconsistent_outcome():
    with pytest.raises(ValueError):
        ToolTrace().record("tool", {}, succeeded=True, error_type="ValueError")


def test_fail_fast_for_invalid_function():
    with pytest.raises(TypeError):
        ToolTrace().invoke("missing", object())
