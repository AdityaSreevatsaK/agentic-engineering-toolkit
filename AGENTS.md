# AET Engineering Reference for Maintainers and AI Coding Agents

> **Document purpose:** Deep, source-grounded technical orientation for a new engineer, reviewer or repository-aware coding agent. Read this before altering AET. It is deliberately more comprehensive than the quick-start README. The canonical behaviour remains the source code and tests. When they disagree with this document, inspect the code, document the discrepancy and fix the documentation rather than assuming the prose is executable truth.
>
> **Repository:** [AdityaSreevatsaK/agentic-engineering-toolkit](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit)  
> **Active product:** Agent Project Scaffolder  
> **Python:** 3.11+; required CI tests 3.11 and 3.12  
> **Current package metadata version:** `aet-scaffolder 0.8.0`, from root `pyproject.toml`  
> **Default branch:** `master`; protected by a GitHub branch ruleset  
> **Licence:** Apache-2.0, with `LICENSE` and `NOTICE` at repository level and in generated projects  
> **Reference checked:** 12 November 2026, baseline `01fba0415fd159439f274341df8ec0194298058c`. Later changes must be validated against their own commit.

## Contents

1. [Identity, scope and value proposition](#1-identity-scope-and-value-proposition)
2. [Architecture and lifecycle](#2-architecture-and-lifecycle)
3. [Repository map and sources of truth](#3-repository-map-and-sources-of-truth)
4. [CLI, generator, registry and Project Doctor](#4-cli-generator-registry-and-project-doctor)
5. [The four generated project types](#5-the-four-generated-project-types)
6. [Provider configuration and adapters](#6-provider-configuration-and-adapters)
7. [Runtime foundations, errors and security boundaries](#7-runtime-foundations-errors-and-security-boundaries)
8. [RAG corpus design, retrieval and invalidation](#8-rag-corpus-design-retrieval-and-invalidation)
9. [Testing architecture and evidence](#9-testing-architecture-and-evidence)
10. [Legacy assets versus the separate AEA project](#10-legacy-assets-versus-the-separate-aea-project)
11. [Installation, operation and troubleshooting](#11-installation-operation-and-troubleshooting)
12. [Extending templates, providers and validation safely](#12-extending-templates-providers-and-validation-safely)
13. [Governance, releases and deployment considerations](#13-governance-releases-and-deployment-considerations)
14. [Known limitations, risks and claims that must not be made](#14-known-limitations-risks-and-claims-that-must-not-be-made)
15. [Coding-agent operating protocol](#15-coding-agent-operating-protocol)
16. [Reference index and maintenance checklist](#16-reference-index-and-maintenance-checklist)

## 1. Identity, scope and value proposition

### 1.1 What AET is

**Agentic Engineering Toolkit (AET)** currently means the **Agent Project Scaffolder**, a local-first Python tool that creates complete, individually installable starter applications for agent-related use cases. A new user selects a framework-oriented template and a supported model-provider configuration, generates the project, validates its structure and syntax, installs its dependencies, runs tests and starts a local FastAPI application.

The reusable asset is **the generation system and its tested reference implementations**. It is not an agent host, common runtime required by generated applications, evaluation server, cloud provisioning stack or ready-made enterprise platform.

The engineering problem is repeated setup work. Teams repeatedly recreate Python packaging, framework imports, example workflows, provider settings, HTTP endpoints, safe local defaults, unit tests, health/readiness behaviour, basic logging, container samples and CI. AET supplies these foundations in a consistent and inspectable starting point so delivery engineers can adapt the generated source to a project.

The codebase is appropriate for technical demonstrations, inspection, architecture discussions and controlled synthetic-data pilots. Its offline correctness is tested. Adoption by independent delivery teams and human productivity improvements have **not** been established.

### 1.2 What AET deliberately does not do

- It does not train, host or manage models.
- It does not provide a live production-ready agent service.
- It does not autonomously plan across arbitrary tools in the `tool-agent` template: order-status routing is deterministic.
- It does not provide semantic embeddings, vector search or document-level authorisation in its current RAG starters.
- It does not assert that synthetic mock answers represent LLM quality, safety or reasoning.
- It does not require cloud credentials, paid API calls, Docker, WSL or an Ollama daemon for the default offline generation and tests.
- It does not implement enterprise authentication, authorisation, tenancy, secrets management, network policy, cloud deployment infrastructure, rate limits, production SLAs or provider-independent model equivalence.
- It is **not** the separate **Agent Engineering Accelerator (AEA)**. AEA owns agent evaluation, LLM-as-judge, statistical comparisons, regression analysis and quality gates. Do not transfer AEA functionality into AET without an explicit architectural decision.
- It does not count passing CI as proof of independent engineer adoption or measurable business productivity.

This scope was formalised in `docs/decisions/0011-scaffolder-focus.md`. Historical evaluation tools remain in the repository for compatibility and provenance, not as an active competing product.

### 1.3 Who uses AET, and why

| Role | Primary activity | Intended benefit | What still requires verification |
| --- | --- | --- | --- |
| Python AI/backend engineer | Generate a known-working tool-agent, LangGraph RAG, Strands or LlamaIndex starter | Avoid repetitive configuration and boilerplate | Fit to client's specific requirements |
| AI solution architect | Inspect alternative runtime/provider arrangements and source boundaries | Compare reproducible choices across frameworks | Security, compliance, deployment and model suitability |
| Delivery technical lead | Review generated API, tests and packaging conventions | Establish a common starting pattern | Independent team adoption and engineering impact |
| Maintainer or AI coding agent | Add a template/provider, fix a bug, update tests/documentation | Make controlled, reviewable changes without breaking old projects | Compatibility, full CI, evidence integrity |
| Controlled pilot reviewer | Execute the fresh-user walkthrough with synthetic data | Reproduce the functionality without author assistance | Genuine observed usability and time measurements |

### 1.4 Primary implementation contracts

AET's main API is a CLI. The generated app, not the generator, owns its runtime endpoint contracts. Distinguish **generation-time provider selection** (which writes an example project configuration) from **runtime inference** (which may require optional SDKs, credentials and network access).

An AET-generated project is meant to be independently usable after generation. It contains its own `app/` Python package, `pyproject.toml`, `tests/`, `README.md`, `.env.example`, GitHub Actions CI, Docker reference and licence/notice files. The generated application **must not** secretly depend on importing `aet_scaffolder` at runtime.

## 2. Architecture and lifecycle

### 2.1 End-to-end control flow

```text
Developer / automation
    |
    | agentkit list / new / doctor
    v
aet_scaffolder.cli (argument parsing, user-facing errors)
    |
    +--> registry.py (supported templates and allowed providers)
    |
    +--> generator.py (validate name/provider/model, stage files,
    |                  substitute four placeholders, write manifest,
    |                  rename staging directory into final project)
    |
    +--> validator.py (read-only Doctor: expected files, manifest,
                       PEP 508 dependencies, .env.example, Python syntax)
    |
    v
New self-contained Python application
    |
    +--> app/config.py : validated runtime settings
    +--> app/main.py : FastAPI /health, /ready and /invoke or /ask
    +--> app/foundation.py : request IDs, sanitised logs/failures
    +--> framework modules : LangGraph / Strands / LlamaIndex
    +--> app/providers.py (+ optional native/cloud model adapters)
    +--> synthetic tools or bounded JSONL knowledge base
    +--> tests/, Dockerfile, pyproject.toml, own CI, README
    |
    v
Run app locally / adapt as a separately governed project
```

These are **two execution boundaries**:

1. **Scaffolding boundary:** AET resolves a registered template and copies text files into a project directory. Generation itself does not invoke a model or install generated-app dependencies.
2. **Generated-application boundary:** The user installs the generated project's dependencies, selects a runtime provider and invokes an actual framework/API implementation. Provider activation happens here.

The generator is **not** a managed deployment service. The developer owns everything after copying and adapting the generated app.

### 2.2 Design principles and rationale

- **Offline first:** mock is the default, safe test mode. Real Ollama and cloud providers are opt-in.
- **Self-contained output:** templates duplicate small support modules on purpose so generated applications work independently. Removing duplication by introducing an AET runtime dependency would violate this contract.
- **Registry-driven extensibility:** `TemplateSpec` is the single inventory of supported template identifiers, providers, required files, required dependencies and expected environment fields.
- **Safe generation:** validate user-supplied project names, reject existing targets and generate in a staging directory rather than overwriting in place.
- **Read-only Doctor:** validate file structure and Python syntax without importing or executing the generated application.
- **Backwards compatibility:** preserve old CLI entry points, the default tool-agent, generated contracts and manifest-less pre-M11 projects.
- **Explicit dependency opt-in:** provider-specific SDK packages belong to the generated project's optional dependency extras.
- **Evidence integrity:** distinguish deterministic code checks, fake SDK constructors, actual framework SDK offline loops, external provider calls, usability trials and measured productivity.

See `docs/decisions/0001-local-first.md`, `docs/decisions/0011-scaffolder-focus.md` and `docs/release/leadership-review.md` for historical rationale and release framing.

## 3. Repository map and sources of truth

```text
/
├── README.md                          # Short, human-friendly project front door
├── AGENTS.md                          # This long-form technical / coding-agent reference
├── pyproject.toml                     # aet-scaffolder build, metadata, console scripts
├── LICENSE, NOTICE, SECURITY.md       # Legal, attribution and disclosure policy
├── .github/workflows/
│   ├── ci.yml                         # Push/PR quality + four OS/Python smoke jobs
│   └── dependency-audit.yml           # Monthly, tag and manual advisory checks
├── src/aet_scaffolder/
│   ├── __main__.py                     # python -m aet_scaffolder
│   ├── cli.py                          # agentkit
│   ├── registry.py                     # TemplateSpec and supported provider matrix
│   ├── generator.py                    # Safe project creation
│   ├── validator.py                    # Read-only Project Doctor
│   ├── benchmark.py, benchmark_cli.py  # Synthetic local operation timings
│   └── templates/
│       ├── tool_agent/
│       ├── langgraph_rag/
│       ├── strands_agent/
│       └── llamaindex_rag/
├── scripts/
│   ├── comprehensive_matrix.py        # Registry-wide offline API matrix
│   ├── deep_event_matrix.py           # Adversarial requests + concurrency + metrics
│   ├── release_smoke.py               # Isolated generated-app ASGI smoke
│   ├── evidence_manifest.py           # SHA-256 report integrity metadata
│   ├── adoption_preflight.py          # Structural trial preparation
│   ├── configure_branch_ruleset.py    # Owner-only ruleset helper
│   └── run_demo.py, evaluate_*.py,
│       analyze_pilot.py, _*_probe.py   # Historical/demo/pilot support
├── tests/                              # Scaffolder, compatibility and governance tests
├── tests/fixtures/                     # Synthetic datasets + pre-M11 project
├── packages/
│   ├── agent-quality-kit/             # Legacy standalone assertions/trace package
│   └── agent-provider-contract/       # Legacy standalone text provider contract
├── examples/                            # Historical integration/contract checks
└── docs/
    ├── decisions/                      # Architecture decision records
    ├── release/                        # Pilot release, review and gate documents
    ├── testing/                        # Matrix, deep-event and audit evidence
    ├── adoption/, pilot/, benchmarks/  # Human trial plans, NOT completed adoption
    ├── architecture/                    # Historical portability reference
    ├── evaluation/, demo/              # M7-M10 historical evidence
    ├── governance/                      # Owner-operated branch protection
    ├── legacy-assets.md
    └── roadmap.md
```

### 3.1 Finding authoritative answers

| Question | Primary source | Corroboration |
| --- | --- | --- |
| Which templates/providers exist? | `src/aet_scaffolder/registry.py` | `tests/test_template_registry.py` and `scripts/comprehensive_matrix.py` |
| Which CLI flags really work? | `src/aet_scaffolder/cli.py` | `tests/test_generator.py` |
| How does copying/manifest work? | `src/aet_scaffolder/generator.py` | `tests/test_generator.py` |
| What does Doctor inspect? | `src/aet_scaffolder/validator.py` | `tests/test_validator.py`, `tests/test_validator_pep508.py` |
| What does an HTTP request do? | Selected `templates/<template>/app/main.py` | Generated tests, runtime modules |
| What cloud integration exists? | Provider/model modules inside **each** generated template | Generated fake-SDK constructor tests |
| How does RAG rank/load documents? | RAG `app/knowledge.py` and `app/retrieval.py` | `tests/test_retrieval.py` in the template |
| What is required to merge? | `.github/workflows/ci.yml` and active GitHub ruleset | Latest actual CI run for the change |
| What tests have **actually** passed? | GitHub Actions run + attached machine evidence | `docs/testing/` reports with run IDs |
| What is the accepted product direction? | `docs/decisions/0011-scaffolder-focus.md` | `docs/roadmap.md` |
| Has productivity or adoption been established? | Authorised external trial records, if any | `docs/adoption/evidence-register.md`; do not infer from CI |
| What is the security disclosure policy? | `SECURITY.md` | Generated readme/foundations |

**Source-precedence rule:** executable source and current test results > current registry/configuration > accepted ADRs > historical documents > this orientation. Older release reports and ADRs can contain accurate historical statements that are **no longer current**. E.g. older governance wording describes an unprotected branch, whereas the active November ruleset protects `master`.

## 4. CLI, generator, registry and Project Doctor

### 4.1 Packaging and entry points

Root `pyproject.toml` uses setuptools with packages under `src/` and bundles `templates/**/*` as package data. Runtime dependency: `packaging>=24,<27` for PEP 508 validation. Python requirement: `>=3.11`.

Installed commands:

| Invocation | Behaviour |
| --- | --- |
| `agentkit --version` | Print installed package version |
| `agentkit list` | List template names and global provider vocabulary |
| `agentkit new NAME` | Generate default `tool-agent` using `mock` |
| `agentkit new NAME --template langgraph-rag --provider mock` | Choose framework-oriented starter and provider |
| `agentkit new NAME --provider ollama --model llama3.2:1b` | Provide a local model identifier; does not download model |
| `agentkit new NAME --output-dir PATH` | Generate under an existing parent directory |
| `agentkit doctor PATH` | Human-readable static checks |
| `agentkit doctor PATH --json` | Machine-readable validation report |
| `python -m aet_scaffolder ...` | Module form of the CLI, including in CI |
| `agentkit-benchmark --runs 10 --warmups 2` | Local generation/validation benchmark, not human time saved |

The global CLI provider vocabulary is broader than some templates. `generator.py` checks support against **the selected template's** `TemplateSpec.providers` and fails on an invalid pairing.

### 4.2 Generation algorithm and invariants

In `generator.generate(name, *, output_dir, template, provider, model)`:

1. Validate `name` using the lowercase kebab-case expression `^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$`. No slash, whitespace, path traversal or arbitrary filename character is permitted.
2. Resolve the requested `TemplateSpec` using `registry.get_template`. Unknown names are rejected.
3. Validate the provider against that specific template. Reject `--model` for every provider other than `ollama`.
4. Validate the selected Ollama model identifier, even when using its default `llama3.2:1b`.
5. Resolve `output_dir` and require that the parent directory exists. **Never overwrite an existing target**.
6. Locate bundled template resources using `importlib.resources.files("aet_scaffolder")`.
7. Create a temporary staging directory beneath the parent, recursively copy template text files and replace four placeholders: `__PROJECT_NAME__`, `__PACKAGE_NAME__`, `__PROVIDER__` and `__OLLAMA_MODEL__`.
8. Convert template file/directory names prefixed `_dot_` to hidden output names: e.g. `_dot_env.example` → `.env.example`, `_dot_gitignore` → `.gitignore`, `_dot_github` → `.github`.
9. Write `.aet-template.json` with `{"schema_version": 1, "template": "<registered-template>"}`.
10. Rename the staged project to the final target; temporary files are cleaned up on exit. An existing destination or filesystem error must never be silently overwritten.

**Interpretation:** the stage-and-rename strategy reduces partially written outputs, but it is not a transactional distributed filesystem guarantee. Do not present it as a security sandbox. `_copy_template` assumes trusted bundled UTF-8 text templates, not arbitrary third-party downloads.

### 4.3 Declarative registry

`TemplateSpec` is an immutable dataclass with:

- `name`: CLI template identifier.
- `directory`: corresponding bundled source directory, using underscores internally.
- `description`: purpose for maintainers.
- `providers`: accepted provider names in this template.
- `required_files`: static Doctor contract.
- `required_dependencies`: canonical baseline distribution names.
- `required_env_fields`: exact lines that must be present in the generated `.env.example`.

`TEMPLATES` is an immutable `MappingProxyType` indexed by name; `SUPPORTED_TEMPLATES` is its tuple of keys. `DEFAULT_TEMPLATE = "tool-agent"`. `MANIFEST_FILE = ".aet-template.json"` and `MANIFEST_VERSION = 1`.

**Do not** hardcode a new template in separate code branches without updating the registry and its full tests. The CLI, generation and validation paths intentionally consume that registry.

### 4.4 Project Doctor in detail

`validate_project(path) -> ValidationReport` returns ordered `Check(name, passed, message)` records and an aggregate `ok` property. Doctor:

1. Rejects missing or symlinked root directories.
2. Reads and validates the manifest. Unknown templates, unsupported schema versions, malformed types and symlinked manifest files fail closed.
3. Checks every registry-required file is a regular, readable, non-symlink file of at most 1 MB.
4. Parses project metadata with `tomllib`, verifies project name and checks that the baseline dependency names exist. PEP 508 packages, optional extras, versions and environment markers are parsed with `packaging.requirements.Requirement`; distribution names are canonicalised.
5. Checks required configuration names appear in `.env.example`. It **does not** verify that real secrets or external providers work.
6. Compiles source under generated `app/` and `tests/` for syntax without importing or executing it.

Legacy behaviour is essential: **pre-M11 manifest-less generated tool-agent projects use a frozen historical validation profile**, not today's stricter foundation-file contract. Older Strands layouts without modern cloud-adapter fields have a separate compatibility path; current Strands projects must not silently pass with a missing cloud adapter.

Doctor does **not** install dependencies, validate actual runtime SDK imports, execute tests, test an LLM, contact cloud APIs, inspect arbitrary other directories or certify an application for production. Its JSON is a structural report only.

---

## 5. The four generated project types

There are **four** templates, representing **three framework families**. Six provider names exist overall; Strands intentionally excludes Ollama. There are **23 declared and supported template/provider combinations**, not 24.

| Template name passed to `--template` | Framework / role | Accepted providers | Main endpoint | Question limit |
| --- | --- | --- | --- | --- |
| `tool-agent` | LangGraph state graph with deterministic synthetic order lookup | mock, ollama, openai, azure-openai, anthropic, bedrock | `POST /invoke` | 4,000 characters |
| `langgraph-rag` | LangGraph local BM25 retrieval and optional answer synthesis | mock, ollama, openai, azure-openai, anthropic, bedrock | `POST /ask` | 2,000 characters |
| `strands-agent` | Actual Strands SDK agent loop and read-only synthetic order-status tool | mock, bedrock, openai, azure-openai, anthropic | `POST /invoke` | 1,000 characters |
| `llamaindex-rag` | Native LlamaIndex keyword-table retrieval and optional synthesis | mock, ollama, openai, azure-openai, anthropic, bedrock | `POST /ask` | 2,000 characters |

All apps have `GET /health` and `GET /ready`. In mock mode `/ready` checks safe local settings and, for RAG, availability of the local knowledge corpus. In non-mock modes `/ready` deliberately returns **503: live model readiness has not been verified**, even when a user might successfully invoke the provider. It is intentionally conservative, not a production readiness probe.

### 5.1 `tool-agent`: deterministic LangGraph order routing

**Source:** `src/aet_scaffolder/templates/tool_agent/`.

Modules and responsibilities:

- `app/main.py`: `InvokeRequest(question)`, `InvokeResponse(answer, tool_used)`, health/readiness and sanitised HTTP exceptions.
- `app/config.py`: per-call Pydantic settings.
- `app/workflow.py`: real LangGraph `StateGraph`, state keys and conditional control flow.
- `app/tools.py`: deterministic, read-only demo order statuses; no real customer integration.
- `app/providers.py`: mock string provider, bounded local Ollama HTTP integration and dispatch into optional cloud provider implementation.
- `app/cloud_providers.py`: lazy LangChain-native SDK models.
- `app/foundation.py`: request logging, IDs and errors.

Graph nodes and transitions:

```text
START
  -> detect_order_request
       | exact regex "order status ORD-####" (case-insensitive)
       +--> lookup_order -> END
       |      get_order_status("ORD-1001") -> shipped
       |
       +--> respond -> END
              selected TextProvider.generate(question)
```

The regex is a **full match** of `order status` followed by a synthetic ID of the form `ORD-1234`. Unknown IDs return an explicit not-found **demo** result. Other input is routed to a text provider, which returns deterministic mock text in mock mode. This demonstrates a simple graph with a tool boundary but **does not implement model-selected dynamic tool planning**.

Typical request:

```json
{"question": "order status ORD-1001"}
```

Typical mock response shape:

```json
{"answer": "Demo order ORD-1001 status: shipped.", "tool_used": "get_order_status"}
```

Do not repurpose `get_order_status` as a real order service without reworking identity, authorisation, customer-data handling, audit and external API failure semantics.

### 5.2 `langgraph-rag`: local BM25 RAG graph

**Source:** `src/aet_scaffolder/templates/langgraph_rag/`.

Modules:

- `app/knowledge.py`: safe bounded JSONL loading, document IDs, metadata-keyed cache.
- `app/retrieval.py`: lexical tokenisation and BM25 ranking, reusable corpus statistics.
- `app/workflow.py`: LangGraph retrieve → respond.
- `app/ingest.py`: optional controlled local `.txt`/`.md` corpus generation.
- `app/providers.py` and `app/cloud_providers.py`: optional local/remote synthesis only after retrieval finds evidence.
- `app/main.py`: `POST /ask` with `answer` and `source_ids`.
- `data/knowledge.jsonl`: fictional example policies and other synthetic source text.

Execution:

```text
POST /ask {"question": "..."}
  -> Pydantic validation
  -> retrieve node:
       read/validate local corpus
       tokenize query and documents
       BM25 score and sort, top-k (default 2)
       collect source {id, text} records
  -> respond node:
       no hits -> explicit no-evidence message
       mock -> quote first retrieved passage with its source ID
       live provider -> compose evidence-restricted prompt
                        -> optional SDK model synthesis
  -> answer + source_ids
```

Important: **source_ids are evidence identifiers, not proof that a generated answer is true**. Real LLM output may ignore citations or instructions. `Mock` demonstrates retrieval; it does not perform generative reasoning. The prompt labels retrieved text as untrusted, but this is not a complete prompt-injection defence.

Request:

```json
{"question": "What is the return policy?"}
```

Response:

```json
{"answer": "Sample retrieved evidence [returns]: ...", "source_ids": ["returns"]}
```

The exact text depends on the bundled or subsequently edited synthetic corpus. Use the actual generated test fixtures rather than hardcoding imagined returns elsewhere.

### 5.3 `strands-agent`: actual SDK agent with deterministic offline model

**Source:** `src/aet_scaffolder/templates/strands_agent/`.

This template is meaningfully different from the LangGraph tool starter. It runs a **real Strands Agent** with a real Strands `@tool` declaration. The bundled `OfflineModel` implements Strands' model streaming interface with scripted events, so it can exercise the SDK's tool-call execution path without sending prompts to AWS or another provider.

Module sequence:

- `app/main.py`: FastAPI endpoint accepts `InvokeRequest(question)`, returns `answer`, `tool_used` (boolean) and `provider`.
- `app/config.py`: constrained model/protocol settings, region, timeouts, model/token options.
- `app/agent.py`: constructs a fresh `strands.Agent` per request, selects the configured model, passes the synthetic tool and detects actual tool-use blocks from agent messages.
- `app/offline_model.py`: scripted `Model.stream` emitting Strands tool-use, final-answer and usage event shapes. It is not an LLM.
- `app/tools.py`: `@tool get_order_status` with validated synthetic IDs.
- `app/cloud_models.py`: lazy Strands-native OpenAI/Anthropic integration and official Azure client injection; Bedrock model selection lives in `agent.py`.
- `app/foundation.py`: same standalone privacy-conscious HTTP foundation.

The mock tool sequence is:

```text
Strands Agent instantiated for request
  -> OfflineModel receives question
  -> if synthetic order command:
       OfflineModel emits structured toolUse event
       Strands SDK invokes @tool get_order_status
       SDK records toolResult
       OfflineModel streams a final response containing tool text
  -> response includes tool_used=true, provider="mock"
```

In contrast, a question without a synthetic matching order command produces the mock instructional response and `tool_used=false`. A **new Agent per request** avoids accidental shared conversation state across distinct HTTP callers; it is not a full state-management solution for multi-turn agents.

Cloud mapping in this template is provider-specific:

- `bedrock` → `strands.models.BedrockModel` with botocore `Config` timeouts and retry policy.
- `openai` → `strands.models.openai.OpenAIModel`.
- `azure-openai` → official `AsyncAzureOpenAI` injected into Strands `OpenAIModel`.
- `anthropic` → `strands.models.anthropic.AnthropicModel`.
- `mock` → local scripted `OfflineModel`.

**Ollama is not an allowed Strands provider** in the current registry; changing that requires new code and tests, not a documentation-only claim.

Example:

```json
{"question": "order status ORD-1001"}
```

Mock response shape:

```json
{"answer": "Sample order ORD-1001 status: shipped.", "tool_used": true, "provider": "mock"}
```

### 5.4 `llamaindex-rag`: native keyword table and optional LLM

**Source:** `src/aet_scaffolder/templates/llamaindex_rag/`.

This is **not** a LangGraph reimplementation. It uses native LlamaIndex `SimpleKeywordTableIndex`, `KeywordTableSimpleRetriever`, `TextNode` and `MockLLM` for offline index construction. The local extractor replaces a default keyword extractor to avoid implicit NLTK downloads; source identities and retrieval remain LlamaIndex-native.

Modules:

- `app/main.py`: `POST /ask`, config, bounded corpus loading, retrieval, mock evidence or optional synthesis.
- `app/knowledge.py`: bounded JSONL parser and metadata-based snapshot cache, paralleling LangGraph RAG's source contract.
- `app/retrieval.py`: keyword extraction, stopword filtering, cached `_OfflineKeywordIndex` and new retriever per query.
- `app/providers.py`: lazy LlamaIndex provider-native model constructors; `synthesise` calls `model.complete` with retrieved text.
- `app/config.py`: local and optional provider settings.
- `data/knowledge.jsonl`: synthetic corpus.

Execution:

```text
HTTP question
  -> load_documents (bounded JSONL, cached immutable documents)
  -> retrieve (native keyword index, top-k)
  -> no source: explicit no-evidence message
  -> mock: quote first retrieved source
  -> opted-in model: LlamaIndex-native complete(prompt)
  -> return answer and source_ids
```

The keyword index is a **lexical** mechanism. Do not call it vector similarity, embeddings, dense retrieval or RAG evaluation. The generated `pyproject.toml` declares optional native integrations separately from its `llama-index-core` base dependency. No model download or cloud call happens during mock retrieval.

### 5.5 Common generated project structure and API semantics

The templates each contain a complete starter in their own directory:

```text
generated-project/
  .aet-template.json         # Registry identity and schema version, no secret
  .env.example               # Committable documented defaults, no real keys
  .gitignore, .dockerignore
  .github/workflows/ci.yml   # Generated project's own offline tests
  pyproject.toml             # Independent app and provider extras
  README.md, LICENSE, NOTICE
  Dockerfile                  # Development reference, not prod security design
  app/                        # API, config, provider, framework, foundation
  tests/                      # Local runtime / contract tests
  data/knowledge.jsonl        # Only present for RAG templates
```

The generated project is a new unit of ownership. Editing a generated copy does **not** update AET's bundled template. Editing the bundled template changes **future generations**, not existing consumer applications. A backward-compatible AET release never silently rewrites previously generated project directories.

## 6. Provider configuration and adapters

### 6.1 Supported model-provider matrix

| Provider | tool-agent | langgraph-rag | strands-agent | llamaindex-rag |
| --- | :---: | :---: | :---: | :---: |
| `mock` | Yes | Yes | Yes | Yes |
| `ollama` | Yes | Yes | **No** | Yes |
| `openai` | Yes | Yes | Yes | Yes |
| `azure-openai` | Yes | Yes | Yes | Yes |
| `anthropic` | Yes | Yes | Yes | Yes |
| `bedrock` | Yes | Yes | Yes | Yes |
| **Total per template** | **6** | **6** | **5** | **6** |

This is **23 declared configurations** and not 23 fully exercised live model services. The comprehensive matrix forces each configured project to **mock** for runtime ASGI probes, while per-template fake-SDK tests validate much of the provider model construction.

### 6.2 Provider implementations are native to each framework

| Template family | Integration mechanism | Where to inspect |
| --- | --- | --- |
| LangGraph tool + RAG | LangChain `ChatOpenAI`, `AzureChatOpenAI`, `ChatAnthropic`, `ChatBedrock` | `app/cloud_providers.py`, plus `providers.py` and `config.py` |
| Strands SDK | `BedrockModel`, Strands `OpenAIModel`/`AnthropicModel` and injected official Azure OpenAI async client | `app/agent.py` and `app/cloud_models.py` |
| LlamaIndex | Native `llama_index.llms` OpenAI, Azure, Anthropic, Bedrock Converse and Ollama clients | `app/providers.py` |
| Default offline | Deterministic mock outputs, or Strands' scripted `OfflineModel` | Provider code / Strands offline-model module |

There is **no single universal runtime adapter object shared by all four frameworks**. This is intentional. The *generator interface* is cross-framework; the output applications remain framework-native, readable and extensible. The historical standalone provider-contract package is a separate compatibility/reference asset, not a dependency secretly imported by every generated service.

### 6.3 Settings, conventions and validation

All generated apps use Pydantic Settings with the `AET_` environment prefix and optional local `.env`. Do not commit actual secret values or use generated `.env.example` as a credential store.

Common and relevant settings:

| Setting | Meaning |
| --- | --- |
| `AET_PROVIDER` | Explicit runtime provider: defaults to generator-selected value, normally mock |
| `AET_LOG_LEVEL` | DEBUG, INFO, WARNING or ERROR for structured request logging |
| `AET_OLLAMA_MODEL` | Local Ollama model identifier; use `--model` only with `--provider ollama` |
| `AET_OLLAMA_BASE_URL` | Explicit loopback HTTP host/port; non-loopback URLs are rejected |
| `AET_OLLAMA_TIMEOUT_SECONDS` | Local Ollama timeout in the LangGraph implementations |
| `AET_KNOWLEDGE_PATH` | RAG local JSONL file path |
| `AET_TOP_K` | Number of lexical retrieval hits, default 2; allowed 1 to 5 |
| `AET_OPENAI_MODEL` | Model identifier for OpenAI native integration |
| `AET_AZURE_OPENAI_DEPLOYMENT` | Azure deployed-model name |
| `AET_AZURE_OPENAI_MODEL` | LlamaIndex Azure model field, additionally used there |
| `AET_AZURE_OPENAI_ENDPOINT` | HTTPS origin without embedded credentials, extra path/query or fragment |
| `AET_AZURE_OPENAI_API_VERSION` | API version string |
| `AET_ANTHROPIC_MODEL` | Anthropic selected model |
| `AET_ANTHROPIC_MAX_TOKENS` | Strands-specific upper limit for Anthropic output |
| `AET_BEDROCK_MODEL_ID` | AWS Bedrock model identifier |
| `AET_AWS_REGION` | AWS region choice; may also be provided via standard AWS SDK environment |
| `AET_MODEL_TIMEOUT_SECONDS` | Bounded cloud/model request timeout |
| `AET_MODEL_MAX_RETRIES` | Available on LangGraph and Strands templates; passed to those model SDKs |

**Not every setting is accepted or used by every template.** The exact generated `app/config.py` and `.env.example` are authoritative. LlamaIndex currently documents model timeout but does not expose the same universal retry field as the LangGraph/Strands starters.

Ollama URL validation rejects public-network endpoints, embedded credentials, custom paths and missing ports. Azure endpoints are constrained to HTTPS origins. These checks mitigate accidental misconfiguration; they do not implement a general outbound-network firewall.

Credentials are resolved by official SDKs or secure process environment/IAM identity. Common names include `OPENAI_API_KEY`, `AZURE_OPENAI_API_KEY`, `ANTHROPIC_API_KEY` and AWS SDK credentials/role mechanisms. Never inject secret values into generated README, sample config, tests, JSONL reports, CI output or repository issues.

### 6.4 Generated dependency extras

Base project installs support default offline execution. Optional extras vary by template:

- LangGraph templates: `.[dev]`, `.[openai]`, `.[azure-openai]`, `.[anthropic]`, `.[bedrock]` and `.[cloud]`.
- Strands: `.[dev]`, `.[openai]`, `.[azure-openai]`, `.[anthropic]` and `.[cloud]`. Bedrock is a supported core Strands SDK path, not necessarily a separate `bedrock` extra.
- LlamaIndex: `.[dev]`, `.[ollama]`, `.[openai]`, `.[azure-openai]`, `.[anthropic]`, `.[bedrock]` and `.[cloud]`.

The `[cloud]` extra bundles optional cloud integration dependencies for the given generated project; it does not make all providers available at runtime without credentials, model access and correct settings. Some SDKs and models also require external network access and billing approval.

### 6.5 Operational limits of a configured provider

The framework-native integrations perform lazy imports or SDK construction when selected. For LangGraph, the cloud constructors pass timeout/retry settings into their native clients; Strands configures SDK client args or botocore timeouts/retries; LlamaIndex passes timeout into its native constructors. Provider-specific exceptions are wrapped into generic user-facing errors rather than exposing SDK payloads.

In any non-mock provider test, distinguish:

1. **Generation passed:** project files were created.
2. **Doctor passed:** source structure and samples are valid.
3. **Fake provider-constructor test passed:** SDK wiring was exercised with fakes.
4. **Local Ollama transport test passed:** loopback request protocol was mocked.
5. **Actual provider inference passed:** an approved live model returned a result, with credential/region/version/cost evidence.

Only the first four have broad automated repository coverage. Do not claim the fifth without a separate authorised live integration run.

## 7. Runtime foundations, errors and security boundaries

### 7.1 HTTP foundation common to all templates

Each generated `app/foundation.py` installs FastAPI middleware with:

- Server-generated random `X-Request-ID`, **not** copied from an arbitrary inbound client header.
- A monotonic `duration_ms` observation.
- One compact structured JSON log record with event, request ID, HTTP method, a **known route name or redacted placeholder**, status and duration.
- A failed-request event for HTTP 5xx outcomes and an optional **exception class name only** for otherwise unhandled exceptions.
- Sanitised unexpected 500 responses of the form `{"detail": "Internal server error"}`.

Never add prompt/answer text, question bodies, arbitrary URL paths, query strings, client IPs, request headers, raw exception messages, tracebacks, account identifiers or credentials to this routine. Existing redaction is intentional and security-tested.

### 7.2 Endpoints are not deployment health guarantees

- `GET /health`: process-level liveness indicator, usually `{"status":"ok"}`. It does not prove model access, external dependencies or security readiness.
- `GET /ready` in mock mode: locally validate settings and, for RAG, that a well-formed corpus is available.
- `GET /ready` outside mock mode: 503 with a generic message indicating live-provider readiness is not verified.
- `POST /invoke`: tool or Strands template. Performs locally bounded request-body validation and runs the selected workflow.
- `POST /ask`: RAG templates. Returns answer plus explicit source IDs.

Request validation errors are rejected by FastAPI/Pydantic, usually HTTP 422 (some malformed input parsing can return 400). Local model/config/corpus failures typically surface as sanitised HTTP 503. Unhandled exceptions surface as sanitised 500. Do not reinterpret success/failure codes or response schemas without corresponding generated tests, Doctor updates where relevant, and a backwards-compatibility decision.

### 7.3 Containers

All four templates include a **development-reference** Dockerfile. The reference uses a Python 3.12 slim base, installs the generated package, sets offline mock defaults, uses a non-root UID (10001), includes a liveness HEALTHCHECK and starts Uvicorn inside the container on port 8000. The container exposes a server internally; the **host-side** Docker port must be bound to loopback, for example:

```powershell
docker build -t aet-local-agent .
docker run --rm -p 127.0.0.1:8000:8000 aet-local-agent
```

Run these commands **from the generated project**. There is no need for Docker or WSL to run the normal local Python mock path. These images are **not** production-certified: dependency/image pinning, scanning, container limits, network policy, secrets injection, external authentication and ingress design remain separate deployment responsibilities.

### 7.4 Threat model boundaries

Current benefits include bounded inputs/corpora, local endpoint validation, optional provider selection, safe error messages and synthetic credentials/data in tests. These do **not** solve enterprise access control. A public production app would need, at minimum:

- an authentication strategy, per-action authorisation and (if relevant) tenant-level isolation;
- secret storage and key rotation; egress and ingress controls; TLS and identity middleware;
- rate limiting, request budgets, cancellation, resource quotas and abuse monitoring;
- a reviewed threat model for tool effects, prompt injection and data exfiltration;
- retrieval document ACLs, source provenance/poisoning controls and tenancy filters;
- provider-level residency, contractual, logging and cost safeguards;
- environment-specific deployment, health/alerting and rollback practices.

The current synthetic order tool is read-only. Allowing arbitrary effectful tools or real customer/enterprise documents changes the threat model significantly.

## 8. RAG corpus design, retrieval and invalidation

### 8.1 JSONL schema and loader

Both RAG templates read `data/knowledge.jsonl` by default, using records containing exactly the required fields `id` and `text` (other record keys are not needed). Example:

```json
{"id": "returns", "text": "Fictional sample return policy text."}
```

Loader contract in both `app/knowledge.py` implementations:

- Corpus must be a regular local file, not a symlink.
- Maximum file size: **1,000,000 bytes**.
- Maximum non-blank records: **200**.
- `id` must be a unique string matching `[A-Za-z0-9][A-Za-z0-9._-]{0,79}`.
- `text` must be a non-empty string of **at most 4,000 characters**.
- Malformed JSONL, duplicate IDs, invalid encodings, empty corpus, excessive file size or invalid structure cause a controlled `KnowledgeError`.
- Documents are immutable dataclass instances; the returned Python list is a fresh container to avoid accidental mutation of shared cached state.

### 8.2 Cached snapshots and corpus changes

`load_documents` resolves paths against the generated project's root and uses an LRU cache with **maxsize 8** keyed by the file's resolved path plus filesystem metadata (mtime in nanoseconds, ctime in nanoseconds, size, inode). The loader uses the cached validated document snapshot when the file has not changed. Subsequent requests can load a changed corpus without restarting the web server when metadata changes.

This is a bounded local design, **not a globally transactional data store or a strong distributed consistency mechanism**. When changing corpus contents concurrently with request handling, prefer an atomic replace of the complete file. On Windows the test harness retries transient sharing violations while atomically replacing corpus files. It verifies eventual final corpus visibility but does not prove correctness for arbitrary external writers.

### 8.3 LangGraph RAG BM25

`app/retrieval.py` lowercases and tokenises words matching `[a-z0-9]+`, computes query-term document frequencies and BM25 scores, excludes zero-overlap documents, sorts by descending score with source ID as deterministic tie-breaker, and returns at most `top_k` hits. `top_k` must be from **1 to 5**; its default is **2**.

The algorithm caches per-document word counters, lengths and average length for immutable document tuples (LRU 8). This accelerates repeated lexical retrieval without changing the deterministic mock output contract.

Consequences:

- The method matches **lexical overlap**, not embeddings or natural-language semantic similarity.
- Tokenisation is deliberately simple and may be weak for non-Latin scripts, synonyms, typos and complex morphology.
- BM25 output is still untrusted content if the underlying corpus is untrusted.
- Source IDs identify evidence, not a guarantee of source quality or answer correctness.

### 8.4 LlamaIndex keyword index

`app/retrieval.py` uses a custom local keyword extractor based on a bounded regex and a static stopword list, while keeping the native LlamaIndex keyword index, retriever and node/source identity. A `MockLLM` is explicitly supplied for index construction to prevent default hosted model resolution. An LRU 8 cache reuses a keyword index for the same immutable document tuple, but a new retriever object is made for each query.

Do not silently replace this with embedding/vector retrieval or a default LlamaIndex global language model: doing so changes dependencies, network behaviour, latency, cost, determinism and testing assumptions.

### 8.5 LangGraph RAG ingestion

`python -m app.ingest --input INPUT_DIR --output NEW_CORPUS.jsonl` is available **only in the LangGraph RAG generated template** at the baseline; do not assume an identical ingest CLI exists in LlamaIndex RAG.

Supported ingestion rules:

- Input directory must exist and cannot be a symlink.
- Accept **1 to 30** immediate local `.txt` or `.md` files.
- Each source must be a readable, non-symlink UTF-8 regular file no larger than **200,000 bytes**.
- Each source is split by whitespace into word-based chunks. Default chunk limit **600 characters**, configurable **100 to 4,000**.
- Over-long individual words, invalid file stems/IDs, duplicated generated IDs, empty result, over **200** resulting records or over **1 MB** of JSONL output are rejected.
- Destination must **not** already exist; ingestion refuses overwrites.

To apply a newly created corpus, set `AET_KNOWLEDGE_PATH` to that file, keeping it under your approved project data governance. Do not import customer secrets or confidential documents into public examples or logs.

---
