# AET: Agent Project Scaffolder

**Generate and test ready-to-run Python agent projects across several frameworks, without rebuilding the same starter code each time.**

**[Get started: Simple step-by-step Windows guide](docs/END_TO_END_RUNBOOK.md)**

Open PowerShell, follow the short setup steps and choose a flow. The guide handles project generation, dependencies, tests and local API checks, with no cloud credentials or paid inference for the default demos.

## What can AET create?

| Template | What it demonstrates |
| --- | --- |
| **Tool Agent** (LangGraph) | A working API with a synthetic order-status tool |
| **LangGraph RAG** | Find answers in sample documents, with BM25 search |
| **AWS Strands Agent** | A real Strands SDK tool loop using a scripted local model |
| **LlamaIndex RAG** | Native keyword search over a sample knowledge base |

Each starter includes its own Python project, API, tests, configuration examples and local development Docker reference.

## Providers

Every template runs with **mock inference** without an API key. Supported optional integrations include **Ollama, OpenAI, Azure OpenAI, Anthropic and AWS Bedrock**, depending on the template. The guide explains which combinations work. Live models require separate provider access and may incur charges.

## Engineering status

- Working **local-first engineering prototype**, not a production-ready agent platform.
- Four template types, with Windows/Linux Python 3.11/3.12 automated tests.
- [Latest engineering evidence and readiness assessment](docs/release/leadership-readiness-2026-11-15.md).
- [GitHub Actions results](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions).

Generated APIs default to an unauthenticated local profile; an opt-in hardened profile adds tenant bearer keys, isolated RAG corpora and process-local request limits, but is not production-certified. Human time savings, independent adoption and multi-team reuse have **not** yet been verified.

## Documentation

- **[Simple beginner's guide](docs/END_TO_END_RUNBOOK.md)**: open PowerShell, paste commands and follow the PASS messages.
- [Detailed manual runbook](docs/END_TO_END_RUNBOOK_DETAILED.md): individual terminal steps, troubleshooting, optional providers and Docker.
- [Architecture and complete project reference](PROJECT_DEEP_DIVE.md).
- [Contributor and coding-agent guidance](AGENTS.md).
- [Independent usability trial protocol](docs/adoption/README.md).

AET is distributed under the [Apache License 2.0](LICENSE). The separate Agent Engineering Accelerator (AEA) handles evaluation and regression testing; AET focuses on **project scaffolding**.

See [hardened profile guidance](docs/security/hardened-profile.md) for deployment controls and limitations.

For production-oriented reproducibility, see [hashed locks and digest-pinned deployment images](docs/reproducible-deployment.md). For manually authorised, paid provider contract tests, see `.github/workflows/live-provider-smoke.yml`. Neither is part of the default offline demonstration.
