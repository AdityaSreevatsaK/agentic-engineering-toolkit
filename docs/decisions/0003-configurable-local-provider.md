# ADR-0003: Configurable mock and local Ollama response providers

Status: Accepted for M2 prototype

## Context

Teams need plug-and-use generated projects without cloud credentials or mandatory model downloads, but some want to demonstrate local LLM responses.

## Decision

Provide two configurations from one `tool-agent` template:

- `--provider mock` (default): deterministic response suitable for demos and automated tests.
- `--provider ollama --model <identifier>`: local text generation through Ollama's POST /api/generate endpoint with stream=false.

A small provider protocol isolates orchestration from inference. Validated Pydantic Settings are generated with the project. Remote/non-loopback Ollama endpoints are rejected. Generated apps use a standard-library HTTP adapter, with failures translated into a sanitized 503 response.

Tool routing remains deterministic and synthetic, so no LLM is trusted to choose or invoke tools in M2. The generated .env.example is optional; defaults are baked into generated code.

## Consequences

Local Ollama runtime and model download are needed for real inference, but not for CI or the mock setup. Provider tests fake HTTP and exercise error handling; a real-model smoke test must be run on an appropriately equipped demo machine. The provider boundary can be extended later with new verified implementations.
