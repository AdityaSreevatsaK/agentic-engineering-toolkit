"""Deterministic Strands Model for offline integration, NOT a language model.

It deliberately emits valid Strands tool-use streaming events so the real
Strands Agent invokes the bundled @tool. No AWS SDK, credentials or network
requests are needed to exercise the agent loop in this mode.
"""
import json
import re
from typing import Any, AsyncIterator

from strands.models import Model

_ORDER = re.compile(r"\s*order\s+status\s+(ORD-[0-9]{4})\s*", re.IGNORECASE)


class OfflineModel(Model):
    def __init__(self) -> None:
        self._config = {"model_id": "aet-offline-scripted", "max_tokens": 256}

    def get_config(self) -> dict:
        return dict(self._config)

    def update_config(self, **model_config: Any) -> None:
        self._config.update(model_config)

    async def structured_output(self, *args: Any, **kwargs: Any) -> AsyncIterator[dict]:
        raise NotImplementedError("The deterministic offline model has no structured output")
        yield {}  # pragma: no cover

    async def stream(self, messages: list, tool_specs: list | None = None,
                     system_prompt: str | None = None, **kwargs: Any) -> AsyncIterator[dict]:
        """Reply once, invoke a tool, or consume its result on the subsequent model turn."""
        last = messages[-1]
        results = [
            block["toolResult"] for block in last.get("content", [])
            if isinstance(block, dict) and "toolResult" in block
        ]
        yield {"messageStart": {"role": "assistant"}}
        if results:
            response_parts = results[0].get("content", [])
            response = next((part["text"] for part in response_parts if "text" in part), "No result")
            yield {"contentBlockStart": {"start": {}}}
            yield {"contentBlockDelta": {"delta": {"text": response}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "end_turn"}}
        else:
            question = "".join(
                block.get("text", "") for block in last.get("content", [])
                if isinstance(block, dict)
            )
            match = _ORDER.fullmatch(question)
            if match:
                yield {"contentBlockStart": {"start": {"toolUse": {
                    "toolUseId": "offline-tool-1", "name": "get_order_status"
                }}}}
                yield {"contentBlockDelta": {"delta": {
                    "toolUse": {"input": json.dumps({"order_id": match.group(1).upper()})}
                }}}
                yield {"contentBlockStop": {}}
                yield {"messageStop": {"stopReason": "tool_use"}}
            else:
                yield {"contentBlockStart": {"start": {}}}
                yield {"contentBlockDelta": {"delta": {
                    "text": "Offline Strands demo: ask 'order status ORD-1001' to execute the synthetic tool."
                }}}
                yield {"contentBlockStop": {}}
                yield {"messageStop": {"stopReason": "end_turn"}}
        yield {"metadata": {
            "usage": {"inputTokens": 1, "outputTokens": 1, "totalTokens": 2},
            "metrics": {"latencyMs": 0}
        }}
