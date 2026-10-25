# ADR-0009: External order-status evaluation without committing licensed records

Status: Accepted for M9 development reference.

## Context

The scaffolder currently uses three synthetic order examples. A realistic public order dataset could exercise more valid IDs and statuses, but Olist's original public dataset is licensed CC BY-NC-SA 4.0 and is not automatically cleared for commercial reuse.

## Decision

Introduce a local CLI that reads **only** order IDs and order statuses from a permitted local CSV, builds a deterministic seeded reservoir sample, generates a temporary agent and tests its real FastAPI/LangGraph routing with injected lookup data and Agent Quality Kit trace assertions.

Use a small fully fabricated Olist-shaped fixture for CI, with aggregate JSON labeling `synthetic`. No external downloads, original rows, sensitive fields, licenses or participant identifiers are placed into the private GitHub repository or CI artifacts.

Report exact-match accuracy and in-process request latency with explicit limitations. Do not present the data evaluation as semantic model accuracy, developer productivity, deployment performance or verified real Olist evaluation until an appropriately licensed local dataset is genuinely evaluated.

## Consequences

Real-data evaluation is an opt-in local action. It requires suitable usage permission and an acquired CSV, not credentials in CI. The original dataset's historical statuses do not imply freshness. The generated application's standard built-in synthetic tool remains unchanged.
