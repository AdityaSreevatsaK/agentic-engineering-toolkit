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
