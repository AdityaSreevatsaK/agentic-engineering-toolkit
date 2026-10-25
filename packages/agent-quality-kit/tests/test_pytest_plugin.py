"""The fixture is independently available through pytest plugin auto-discovery."""
from aet_quality import ToolTrace, assert_tool_called


def test_fixture_is_available_and_isolated(agent_trace):
    assert isinstance(agent_trace, ToolTrace)
    assert agent_trace.calls == ()
    agent_trace.record("sample", {"id": "synthetic"})
    assert_tool_called(agent_trace, "sample", arguments={"id": "synthetic"})


def test_each_test_receives_a_fresh_trace(agent_trace):
    assert agent_trace.calls == ()
