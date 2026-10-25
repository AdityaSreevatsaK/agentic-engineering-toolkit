# ADR-0006: Standalone text-provider contract before cloud adapters

Status: Accepted for M6 reference implementation

## Context

The scaffolder's generated FastAPI application already supports mock and loopback Ollama responses behind `generate(str) -> str`. We want a provider-neutral architecture without imposing cloud SDKs, account access, mandatory WSL, or incompatible changes on existing generated projects.

## Decision

Add a standalone `aet-provider-contract` package, separated from the scaffolder and Agent Quality Kit. Define typed `GenerateRequest` and `GenerateResponse`, a `TextProvider` protocol, a deterministic mock and a local Ollama reference adapter. Use injected transport to contract-test Ollama without connecting to a real service. Provide `LegacyTextAdapter` to bridge current generated project providers without requiring them to depend on this package.

Cloud mappings remain documented **concepts only**. Do not commit deployable AWS/Azure/GCP adapters without credentials/budget/privacy approval and provider-specific tests.

## Trade-offs

- The contract focuses only on basic single-turn text; it cannot express tool calls, streaming, multi-turn history or token usage yet.
- Generated projects stay self-contained, avoiding any new runtime dependency on the reference package.
- The bridge and tests establish shape compatibility, not behavioral equivalence among models.
- A live local Ollama smoke test and any real cloud integration require a separate approved environment and are not CI gates at M6.
