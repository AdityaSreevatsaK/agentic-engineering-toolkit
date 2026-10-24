# ADR-0002: Deterministic tool-use reference application

Status: Accepted for M1 prototype

## Context

The original M1 template only echoed inputs and did not demonstrate a tool-using agent, despite the `tool-agent` template name. Adding an actual LLM at this stage would introduce credentials, runtime requirements and non-deterministic tests.

## Decision

Implement a sample local order-status tool backed by synthetic data. A deterministic LangGraph routing node recognises the exact command `order status ORD-1001` (and similar IDs) and calls the tool. Other input uses the existing mock fallback. Return `tool_used` in the API response so the executed path can be verified.

## Trade-offs

This proves workflow integration and testability, not LLM tool selection or real business capabilities. Every branch is covered by generated-app tests. No customer records, model downloads or network connections are necessary for runtime execution.
