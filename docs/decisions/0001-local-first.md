# ADR-0001: Local-first generation and deterministic default

Status: Accepted for M1 prototype (2026-10-24)

## Context
The toolkit must work on native Windows Python without WSL, external cloud platforms, API keys, or an available local model. The repository must remain private.

## Decision
Ship one `tool-agent` template with `mock` as the default and only provider. Use LangGraph to orchestrate the mock workflow and FastAPI to expose an HTTP interface. Use standard-library generation for M1 to keep the scaffolder independently smoke-testable without installing external templating engines. Consider Copier when template lifecycle/version upgrades become necessary.

## Consequences
A generated environment still requires standard Python dependencies from an approved package source. Offline model inference is not part of M1. Default API responses are synthetic. No claims about cloud portability, enterprise security or production readiness are made.
