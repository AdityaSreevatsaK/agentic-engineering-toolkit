# ADR-0007: Local offline demo as adoption-readiness evidence

Status: Accepted for M7 prototype

## Decision

Add a repeatable single-command demonstration that generates a mock project in a temporary directory, runs static validation and tests actual in-process FastAPI behavior through an isolated Python interpreter. Verify the standalone Agent Quality Kit's tool-call assertions and the Portable Provider Contract's typed mock, compatibility bridge and fake local Ollama adapter.

Do not introduce cloud accounts, model downloads, public HTTP listeners, telemetry or side effects on the user's development project. Capture only sanitized pass/fail information; keep the generated workspace temporary.

## Evidence boundary

Passing GitHub Actions and this demo proves a reproducible software integration for the exact tested versions and environments. It does not establish cross-team adoption, production readiness, cloud backend functionality, human time saved, or LLM output correctness. Independent reviewer feedback and controlled productivity trials require separate, approved participation.
