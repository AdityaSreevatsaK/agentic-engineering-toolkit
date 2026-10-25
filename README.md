# AET: Agent Project Scaffolder

**Status:** Working local-first engineering prototype; **not** a production-ready agent platform.
**Access:** Private repository. Do not make it public or commit client data, employer-owned code, credentials or secrets without approval.

AET is a **project scaffolder for Python agent applications**. It generates self-contained starter projects that engineers can run, test and adapt. Its job is to reduce repeated project setup work and establish consistent application foundations, not to evaluate model quality or operate production infrastructure.

The separate **Agent Engineering Accelerator (AEA)** owns LLM/agent evaluation, regression analysis, statistical testing, LLM judging and quality gates. AET does not recreate those functions, and does not currently depend on AEA.

## What AET generates today

| Template | Status | Generated application | Providers |
| --- | --- | --- | --- |
| tool-agent | Working prototype | FastAPI + LangGraph with deterministic synthetic order-status routing | Mock (offline), optional local Ollama |
| langgraph-rag | Planned M12 | Runnable LangGraph retrieval-augmented application | To be defined and tested |
| strands-agent | Planned M13 | Runnable AWS Strands agent reference | To be defined and tested |

The current tool-agent is **not** an autonomous tool-planning agent. Its order routing is deterministic. No cloud account, paid model, Docker or WSL is needed for the mock path. The generated API has no authentication and must not be exposed publicly.

## Start here

Python 3.11+ on Windows or Linux:

~~~powershell
python -m pip install -e .
agentkit list
agentkit new demo-agent --provider mock
agentkit doctor demo-agent
cd demo-agent
python -m pip install -e ".[dev]"
python -m pytest -q
python -m uvicorn app.main:app --reload
~~~

Open http://127.0.0.1:8000/docs and send POST /invoke with the body:

~~~json
{"question": "order status ORD-1001"}
~~~

The tool path looks up only fabricated local order statuses. Other prompts use a deterministic mock response by default. To generate an optional local Ollama project:

~~~powershell
agentkit new local-agent --provider ollama --model llama3.2:1b
~~~

Real model responses require independently installing and running Ollama with the named model. Automated tests mock its HTTP interactions; no model download is required in CI.

## Commands and compatibility

| Command | Purpose |
| --- | --- |
| agentkit list | Show registered templates and supported providers |
| agentkit new NAME [--template tool-agent] [--provider mock or ollama] | Create a project without overwriting an existing path |
| agentkit doctor PATH [--json] | Read-only structure, configuration and Python syntax checks |
| agentkit-benchmark --runs 10 --warmups 2 | Measure local generation and validation timings |

Generated projects include a small .aet-template.json manifest so Doctor selects the correct registered template profile. **Older projects without the manifest continue to use the original tool-agent validation profile.** The existing CLI entry points, defaults and package name (aet-scaffolder) are retained.

Doctor does not install dependencies, run untrusted generated Python code, validate real model behaviour or certify security. The benchmark measures file generation and static validation, **not developer hours saved**.

## Engineering foundations and planned scope

- **M11:** Align the active product around scaffolding; introduce a template registry, backwards-compatible validation and clear asset boundaries.
- **M12:** Add a genuine working LangGraph RAG starter with local/mock verification.
- **M13:** Add a genuine working AWS Strands starter, with offline test doubles where cloud access is unavailable.
- **M14:** Improve generated applications' configuration, structured logging, error-handling, CI and deployment foundations.

See [roadmap](docs/roadmap.md), [M11 decision record](docs/decisions/0011-scaffolder-focus.md) and [legacy assets](docs/legacy-assets.md).

## Verification

The private GitHub Actions workflow runs a four-job matrix: Windows/Linux, Python 3.11/3.12. It verifies the scaffolder, generated applications, distribution wheels, and historical independent packages and integrations to protect backwards compatibility.

~~~powershell
python -m pip install -e . pytest
python -m pytest tests -q
~~~

Tests for a freshly generated application live inside that application. CI verifies the mock and Ollama-generated projects without external credentials.

## Historical work (M1-M10)

Earlier AET milestones also delivered an independently packaged Agent Quality Kit, Portable Provider Contract, integration demonstrations, pilot protocols and public-data evaluation. Those are **preserved for provenance and regression compatibility**, but are not active AET product lines. AEA, maintained separately, is the intended evaluation product.

The official NYC 311 test verified deterministic generated-app routing against 100 selected public statuses on 25 October 2026, but did not assess semantic agent intelligence or developer productivity. The source and qualifications remain in [historical evaluation evidence](docs/evaluation/nyc311-verified-results-2026-10-25.md).

**Business impact is not yet proven:** multi-team adoption, independently reproduced onboarding gains, measured time savings, employer approval and production usage require separate evidence. Do not claim these from passing CI or synthetic demos.
