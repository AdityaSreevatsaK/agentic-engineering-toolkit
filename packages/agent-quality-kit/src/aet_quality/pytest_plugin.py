"""Optional pytest integration, auto-loaded when pytest discovers this distribution."""
import pytest

from .trace import ToolTrace


@pytest.fixture()
def agent_trace() -> ToolTrace:
    """An isolated empty ToolTrace per test."""
    return ToolTrace()
