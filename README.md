# AET: Agent Project Scaffolder

**Status:** Working local-first engineering prototype; **not** a production-ready agent platform.
**Access:** Public repository, licensed under [Apache License 2.0](LICENSE). Publication does not imply production readiness or permission to include client data, employer-owned code, credentials or secrets.

AET is a **project scaffolder for Python agent applications**. It generates self-contained starter projects that engineers can run, test and adapt. Its job is to reduce repeated project setup work and establish consistent application foundations, not to evaluate model quality or operate production infrastructure.

The separate **Agent Engineering Accelerator (AEA)** owns LLM/agent evaluation, regression analysis, statistical testing, LLM judging and quality gates. AET does not recreate those functions, and does not currently depend on AEA.

Under Apache 2.0, others may reuse, modify and distribute this code, including commercially, provided they comply with the licence and attribution requirements. The licence does **not** guarantee production readiness or cover third-party dependencies under different licences. Each newly scaffolded project includes its own LICENSE and NOTICE.

## What AET generates today

| Template | Status | Generated application | Providers |
| --- | --- | --- | --- |
| tool-agent | Working prototype | FastAPI + LangGraph with deterministic synthetic order-status routing | Mock (offline), optional local Ollama |
| langgraph-rag | M12 reference implementation | LangGraph with local BM25 retrieval, evidence-based answers and optional Ollama | Mock (offline), optional local Ollama |
| strands-agent | M13 reference implementation | Real Strands Agent with synthetic tool, deterministic SDK offline model or AWS Bedrock | Mock (offline), optional Bedrock |

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

## Generate the LangGraph RAG application (M12)

~~~powershell
agentkit new knowledge-agent --template langgraph-rag --provider mock
agentkit doctor knowledge-agent
cd knowledge-agent
python -m pip install -e ".[dev]"
python -m pytest -q
python -m uvicorn app.main:app --reload
~~~

Then submit `POST /ask` with `{"question":"What is the return policy?"}`. The bundled corpus uses invented policies and a real BM25 lexical retriever, followed by a **deterministic mock answer** quoting retrieved evidence. Optional `--provider ollama` enables genuine local-model synthesis over that evidence. It is **not** a semantic-vector search template, a claim of model correctness, or a production-secure service. The generated README documents bounded local file ingestion and its limits.

## Generate an AWS Strands agent (M13)

~~~powershell
agentkit new strata-demo --template strands-agent --provider mock
agentkit doctor strata-demo
cd strata-demo
python -m pip install -e ".[dev]"
python -m pytest -q
python -m uvicorn app.main:app --host 127.0.0.1 --reload
~~~

Call POST `/invoke` with `{"question":"order status ORD-1001"}`. The scripted offline model instructs the **real Strands SDK agent loop** to invoke a read-only synthetic `@tool`; the resulting answer reports `tool_used`. The model is deterministic and is **not** an LLM or evidence of autonomous reasoning. For actual Amazon Bedrock inference, use `agentkit new strata-bedrock --template strands-agent --provider bedrock`, then configure approved AWS credentials, region and model access. CI uses injected model doubles, never live AWS calls. See the generated project's README.


## Generated application foundations (M14)

All three templates now produce a small, self-contained engineering foundation:

| Foundation | Included behaviour |
| --- | --- |
| Validated settings | `AET_LOG_LEVEL` and existing provider-specific environment settings |
| Structured logs | Server-issued request ID and JSON metadata only, without prompts/answers/secrets |
| Health and readiness | `GET /health` (process liveness); `GET /ready` (offline/local checks only) |
| Error handling | Stable sanitised HTTP failures; no raw exception details returned |
| Generated CI | A per-project GitHub Actions workflow running offline tests |
| Container reference | Non-root Python 3.12 image, localhost-only host port guidance, Docker healthcheck |

The generated Dockerfile is a **development reference, not a production deployment**. The apps lack authentication, tenancy and cloud-specific hardening. For an offline local example, run `docker build -t aet-demo .` in the generated project, then `docker run --rm -p 127.0.0.1:8000:8000 aet-demo`. See the generated README and [ADR-0014](docs/decisions/0014-generated-app-foundations.md) for details.

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
- **M12:** Add a working LangGraph RAG starter with local BM25 retrieval, offline verification and optional loopback Ollama inference.
- **M13:** Generate a Strands SDK Agent with one synthetic tool, actual offline SDK-loop tests and opt-in Bedrock model.
- **M14:** Add generated configuration validation, privacy-conscious JSON request logs, readiness, CI and non-root local Docker foundations.

See [roadmap](docs/roadmap.md), [M11 decision record](docs/decisions/0011-scaffolder-focus.md) and [legacy assets](docs/legacy-assets.md).

## Verification

GitHub Actions runs a four-job matrix: Windows/Linux, Python 3.11/3.12. It verifies the scaffolder, generated applications, distribution wheels, and historical independent packages and integrations to protect backwards compatibility.

~~~powershell
python -m pip install -e . pytest
python -m pytest tests -q
~~~

Tests for a freshly generated application live inside that application. CI verifies the mock and Ollama-generated projects without external credentials.

## Historical work (M1-M10)

Earlier AET milestones also delivered an independently packaged Agent Quality Kit, Portable Provider Contract, integration demonstrations, pilot protocols and public-data evaluation. Those are **preserved for provenance and regression compatibility**, but are not active AET product lines. AEA, maintained separately, is the intended evaluation product.

The official NYC 311 test verified deterministic generated-app routing against 100 selected public statuses on 25 October 2026, but did not assess semantic agent intelligence or developer productivity. The source and qualifications remain in [historical evaluation evidence](docs/evaluation/nyc311-verified-results-2026-10-25.md).

**Business impact is not yet proven:** multi-team adoption, independently reproduced onboarding gains, measured time savings, employer approval and production usage require separate evidence. Do not claim these from passing CI or synthetic demos.
