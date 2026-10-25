# ADR-0014: Shared foundations in generated applications

**Status:** Accepted in M14
**Scope:** All three active AET scaffolder templates (tool-agent, langgraph-rag, strands-agent)

## Context

M11–M13 established working scaffolded applications but each lacked consistent
HTTP request identification, privacy-conscious logging, readiness validation,
standalone project CI and a reproducible container starting point.

## Decision

1. Every new generated project includes a **self-contained** `app/foundation.py`:
   server-generated `X-Request-ID`, one structured JSON access record per HTTP
   request, monotonic duration and sanitised unexpected-error responses.
   This writes **neither prompts nor response bodies**, request headers, query
   strings, client addresses, raw unmatched URL paths or exception strings.
2. Each generated application's validated `Settings` includes `AET_LOG_LEVEL`.
   Valid log levels are DEBUG, INFO, WARNING and ERROR.
3. Preserve current endpoint contracts. Add a distinct `GET /ready` endpoint:
   mock mode checks local configuration; the RAG template additionally checks
   its local corpus. Opt-in Ollama/Bedrock modes return 503 because real model
   availability is **not verified**. `GET /health` remains process liveness.
4. Add a minimal generated-app GitHub Actions workflow (Python 3.12, offline
   mock tests, read-only checkout permissions).
5. Add a **development reference** Dockerfile (Python 3.12 slim, non-root UID
   10001, liveness HEALTHCHECK, mock provider) and .dockerignore that prevents
   .env secrets entering the build context. In RAG, exclude locally ingested
   data, while retaining the fabricated starter corpus.
6. Make these files part of the registered Project Doctor validation profile.
   Existing generated projects are not modified automatically.
7. Run generated runtime tests for all three templates on Windows/Linux
   Python 3.11/3.12, verify scaffolder wheel content, and smoke-test a generated
   Docker image on Ubuntu in the repository CI.

## Limits / non-goals

- This is not an authenticated, publicly deployable platform. Bind public-facing
  host ports to localhost only; adding real auth, tenancy, ingress policies,
  network egress restrictions, secrets management and threat modelling remains
  the adopting team's responsibility.
- JSON logs intentionally provide minimal metadata, not distributed tracing.
- `GET /ready` does not contact paid/cloud models, so it is not a live model
  SLA/availability probe.
- No managed deployment resources (ECS/EKS/Terraform) or cloud credentials
  are introduced. The container is a local foundation, not a deployment claim.
- Previous generated projects remain unchanged and supported by the
  historical Doctor fallback.
- AEA is separate; no evaluation metrics, LLM judging or quality gates are
  duplicated.
