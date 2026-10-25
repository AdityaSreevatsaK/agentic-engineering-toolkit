"""Explicit opt-in tool-call capture with no agent SDK dependency."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, TypeVar

_T = TypeVar("_T")


@dataclass(frozen=True)
class ToolCall:
    """A deterministic snapshot of a single tool invocation."""

    name: str
    arguments: dict[str, Any]
    succeeded: bool = True
    error_type: str | None = None


class ToolTrace:
    """Collects only calls explicitly recorded or invoked through this instance.

    The trace never logs prompts, credentials, or raw tool results automatically.
    Avoid recording sensitive tool arguments in your tests.
    """

    def __init__(self) -> None:
        self._events: list[ToolCall] = []

    @property
    def calls(self) -> tuple[ToolCall, ...]:
        """Return detached event snapshots to prevent external mutation of history."""
        return tuple(deepcopy(event) for event in self._events)

    def record(
        self,
        name: str,
        arguments: Mapping[str, Any] | None = None,
        *,
        succeeded: bool = True,
        error_type: str | None = None,
    ) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("tool name must be a non-empty string")
        if arguments is not None and not isinstance(arguments, Mapping):
            raise TypeError("tool arguments must be a mapping")
        if not isinstance(succeeded, bool):
            raise TypeError("succeeded must be boolean")
        if error_type is not None and (not isinstance(error_type, str) or not error_type.strip()):
            raise ValueError("error_type must be a non-empty string when provided")
        if succeeded and error_type is not None:
            raise ValueError("successful tool calls cannot have error_type")
        self._events.append(
            ToolCall(
                name=name,
                arguments=deepcopy(dict(arguments or {})),
                succeeded=succeeded,
                error_type=error_type,
            )
        )

    def invoke(self, name: str, function: Callable[..., _T], /, **kwargs: Any) -> _T:
        """Run a tool with keyword arguments; record success/failure and preserve errors."""
        if not callable(function):
            raise TypeError("function must be callable")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("tool name must be a non-empty string")
        try:
            result = function(**kwargs)
        except Exception as exc:
            self.record(name, kwargs, succeeded=False, error_type=type(exc).__name__)
            raise
        self.record(name, kwargs, succeeded=True)
        return result

    def clear(self) -> None:
        self._events.clear()
