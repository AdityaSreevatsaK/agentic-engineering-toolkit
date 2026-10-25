# ADR-0013: AWS Strands SDK agent project template

Status: Accepted for M13 implementation

## Motivation

AET requires a runnable AWS Strands application scaffold distinct from the existing LangGraph tool and RAG starters. The template must demonstrate real SDK object construction and tool invocation without needing AWS credentials in CI.

## Decision

- Introduce `strands-agent` with two provider modes: `mock` (default, fully offline), and `bedrock` (explicit opt-in).
- Both modes instantiate `strands.Agent` and a tool decorated with `@strands.tool`. The bundled tool only reads synthetic order statuses.
- `OfflineModel` implements the Strands `Model` contract and emits deterministic tool-use streaming events. This is scripted SDK integration, **not** an LLM and not a quality evaluation framework.
- Bedrock mode constructs `strands.models.BedrockModel` with configurable model ID and AWS region. Actual AWS model invocation requires access, IAM permissions and budget not supplied or validated by CI.
- Keep a new Agent per HTTP request, don't carry conversation state across users, and sanitise failures at the HTTP boundary.
- Test real offline SDK tool execution, API schema, fake Bedrock construction, provider restrictions, Project Doctor and wheel packaging on Windows/Linux Python 3.11/3.12.
- Do not integrate or duplicate AEA's agent evaluation and CI quality gates.

## Limits

No live Bedrock call, cloud IAM validation, persistent memory, tools beyond synthetic lookups, production auth, model reliability proof, or production deployment. M14 will improve generated application configuration, logging and error handling. Existing AET generated projects and old package interfaces remain supported.
