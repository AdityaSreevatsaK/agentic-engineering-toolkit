"""Framework-independent deterministic assertions for agent integrations.

The core package has no dependencies on agent orchestration frameworks or models.
"""
from .assertions import (
    assert_json_serializable,
    assert_only_tools,
    assert_output_contract,
    assert_tool_called,
    assert_tool_outcome,
    assert_tool_sequence,
)
from .trace import ToolCall, ToolTrace

__version__ = "0.1.0"
__all__ = [
    "ToolCall",
    "ToolTrace",
    "assert_json_serializable",
    "assert_only_tools",
    "assert_output_contract",
    "assert_tool_called",
    "assert_tool_outcome",
    "assert_tool_sequence",
]
