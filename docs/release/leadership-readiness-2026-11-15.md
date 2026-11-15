# AET engineering leadership-readiness assessment

**Evidence cutoff:** 15 November 2026 (Asia/Kolkata). **Source commit:** [`78a6dd6`](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/commit/78a6dd601bb5dd948ec8086cab46b7e5dd676825). **Product:** AET Agent Project Scaffolder, v0.8.0. **Audience:** technical architecture reviewer / reusable-assets decision-maker. **Use:** personal, public, synthetic-only engineering evidence; no employer endorsement is implied.

## Executive decision

**Conditional GO for a technical architecture demonstration and preparation for a controlled, authorised, synthetic-data pilot. NO GO for production deployment, proven developer-productivity improvement, or claimed multi-team adoption.**

The architecture, packaging, generation safety, four generated applications and cross-platform CI evidence are substantial enough to invite technical review. The business-impact outcomes needed for an organisation-wide reusable engineering asset have **not yet been independently established**. A passing pipeline is not an approval from leadership or a security authority.

| Decision dimension | Evidence-backed status | Consequence |
| --- | --- | --- |
| Scaffold/framework implementation | **Verified as a working offline prototype** | Show generated applications, CLI/Doctor, independent installation and automated CI |
| Framework approval by a responsible stakeholder | **Not collected** | Request a review decision; do not write “approved framework” |
| Automated functional and negative-case quality | **Verified for the stated synthetic/mock scope** | Present actual CI artefacts and technical trade-offs |
| Active developer setup time saved | **Not measured** | Never infer human productivity from generation timings or CI duration |
| Independent unfamiliar-engineer usability | **Not validated** | Author self-tests are preparation, not an independent trial |
| Adoption by multiple delivery teams | **Not demonstrated** | Require authorised team/project evidence, not GitHub stars/downloads |
| Production/security/cloud suitability | **Not established** | Keep generated APIs local and unauthenticated only in controlled demo conditions |

## What is built

- **One developer entry point:** `agentkit list`, `agentkit new` and read-only `agentkit doctor`, with declarative template/provider compatibility and safe, non-overwriting atomic publication.
- **Four self-contained application starters:** `tool-agent` (LangGraph deterministic synthetic order routing), `langgraph-rag` (BM25 lexical RAG), `strands-agent` (real Strands SDK loop with scripted mock model), and `llamaindex-rag` (native LlamaIndex keyword RAG). No shared AET runtime dependency is required by generated applications.
- **Configurable integration choices:** mock mode for every starter; Ollama where supported; optional framework-native OpenAI, Azure OpenAI, Anthropic and/or Bedrock integrations by template. Offline SDK fakes test configuration and constructor wiring; **no live hosted-provider inference is validated**.
- **Developer foundations:** per-template tests and CI, typed configuration, local FastAPI health/readiness endpoints, sanitised structured logging, bounded synthetic JSONL RAG files, non-root development Docker examples and Apache-2.0 distribution materials.
- **Clear boundary:** agent evaluation and regression scoring are separate concerns, not features of the AET scaffolder.

## Verified evidence register

Every number below is scoped to the cited execution. Counts across different environments are repetitions of tests, **not distinct use cases or human adopters**.

| Claim permitted | Measured evidence | Primary source and limits |
| --- | --- | --- |
| Latest merged `master` passes all protected CI checks | **5/5 successful:** Ruff/mypy/Bandit, Windows Python 3.11/3.12, Ubuntu Python 3.11/3.12 | [Post-merge run #43630438965](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions/runs/43630438965), at `78a6dd6` |
| Registry configurations are exercised offline | **23/23** declared template/provider pairs on each of **four** OS/Python legs, **92 environment-pair executions** | `comprehensive-matrix-*` artefacts in [run #43630438965](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions/runs/43630438965); configured cloud choices are forced to mock for the HTTP probes |
| Adversarial and concurrency acceptance passes | **716/716** synthetic scenarios per OS/Python leg, **2,864 environment-scenario executions** | `deep-event-*` JSON/CSV/manifest artefacts in the same run; bounded requests, not sustained load or full application-security assessment |
| Windows corpus-swap regression stress passes | **16/16** fresh Windows Python 3.12 trials: 8 LangGraph + 8 LlamaIndex | `corpus-race-stress-windows-2025-py3.12` artefact and [run logs](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions/runs/43630438965), using mock inference. An earlier intermittent failure motivated [PR #41](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/pull/41) and [PR #42](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/pull/42); these runs do not prove all races impossible |
| New generated projects genuinely install in separate environments | **Four independently installed/tested virtual environments on each of four legs**, **16 isolated installs** | `isolated-install-*` artefacts, per-app `pytest`, `pip check`, mock ASGI probes and `pip freeze` captured in [run #43630438965](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions/runs/43630438965) |
| Container examples build and answer local HTTP probes | **Four Docker images**, Ubuntu Python 3.11 job only | Log passes for all four template names in [run #43630438965](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions/runs/43630438965); loopback only, mock, dev images, not production deployment |
| Resolved third-party packages had no reported public advisories at scan time | Four Linux Python 3.12 resolved environments; **381 environment-specific third-party package entries, 0 advisories**, `pip check` 4/4 | [Dependency audit #43587760145](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions/runs/43587760145) and [dated security report](../testing/dependency-security-audit-2026-11-14.md). Repeated packages are counted per environment, eight local package entries are skipped; **not a security certification or perpetual clearance** |
| Source/packaging correctness and publication safety have regression evidence | Cross-platform CI and narrowly scoped direct Linux publication race fixture | [PR #37](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/pull/37), [engineering notes](../testing/atomic-publication-docker-2026-11-14.md); filesystem/platform limitations remain |
| CI scheduling has been benchmarked without deleting tests | Linux isolated-install stage improved in one comparison: Ubuntu 3.11 **65.5s to 60.8s**, Ubuntu 3.12 **70.0s to 47.0s** | [PR #40](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/pull/40), [timing analysis](../testing/ci-efficiency-2026-11-14.md). Windows remains sequential, runner noise exists, **no measured overall workflow speed-up or human setup saving** |

**Evidence provenance:** GitHub workflow IDs, job names, source SHA and artefact names are supplied so reviewers can reproduce the classification. GitHub artefacts have finite retention; follow original runs before expiry. Test code and docs are in the public repository, but successful automation is not independent end-user acceptance.

## Reusable-assets outcome gates

The three reusable-asset outcomes must be evaluated separately:

| Outcome | Threshold to claim success | Current position |
| --- | --- | --- |
| **Approved reusable framework** | A named, authorised technical/asset owner reviews the scoped interface and explicitly accepts it for a specified use | **Implementation exists; approval uncollected** |
| **Measurable developer impact** | Predeclared matched manual-versus-scaffolder task, independently recorded active and wait times, successful outcomes/failures, comparable environment and study limitations | **Protocol and analyser exist; no valid human timing observations** |
| **Multi-team adoption** | At least two independent authorised delivery teams confirm specific uses, project context, adoption date and continued usage or documented outcome | **No such confirmations** |

Avoid treating four different templates, 23 configured pairs, 16 CI virtual environments, repository activity or machine speed as evidence of the second or third gate.

## Technical constraints and non-negotiable controls

1. **Network / tenancy:** Generated APIs have no authentication or tenancy policy. Bind to `127.0.0.1` for demonstrations. Do not publish to public ingress or use customer datasets.
2. **Provider integrations:** SDK configuration and injected doubles establish wiring, not approved cloud deployment, identity permissions, retry behaviour under real service faults, billing limits or LLM answer quality.
3. **Retrieval and data access:** RAG is bounded lexical/keyword retrieval over synthetic local JSONL. It has no semantic vector search, document-level ACL, multi-tenant data separation or enterprise content governance.
4. **Supply chain:** Advisory checks are time- and environment-specific, currently Linux/Python 3.12; generated dependencies are version-ranged rather than a universal immutable lock, so future resolutions may differ. Re-audit before releases.
5. **Windows corpus race:** Writer and reader now use bounded Windows-specific transient-access retries, retaining strict failures on malformed data. The actual historical race has a plausible reader-side cause supported by post-#41 diagnostics, but no proof it can never recur. Preserve stress test and sanitised categorical failure fields.
6. **IP, permissions and privacy:** This is a public personal artefact. Approval for organisational use, ownership/licensing review and permitted data handling are separate prerequisites, never inferred from the Apache licence.

## Low-dependency next steps (no reviewer presently available)

These actions can be completed by one maintainer without fabricating adoption:

| Order | Task and explicit output | Suggested effort | Acceptance |
| --- | --- | --- | --- |
| 1 | Freeze a review baseline: identify commit/release candidate, archive CI IDs, current threat/limitation list, and all four template examples | 1–2 hours | Reproducible reviewed SHA, no hidden paid inference, green required CI |
| 2 | Rehearse a **self-operated** fresh Windows local walkthrough with mock mode and no WSL, then record friction, exact commands, failures and documentation changes | 2–3 hours | Generated RAG service starts; `/ask` before and after synthetic corpus change; all tests pass; observations explicitly labelled **author-run** |
| 3 | Prepare a short architecture decision pack: problem, generator/registry/Doctor data flow, one RAG plus one Strands demonstration, supported provider table, test evidence and red lines | 1–2 hours | A reviewer could assess suitability without a live walkthrough or access to non-public data |
| 4 | If a real reviewer becomes available later, use the unchanged [fresh-user protocol](fresh-user-walkthrough.md) and [private observation form](reviewer-notes-template.md) | External dependency; unscheduled | Record genuine unfamiliar-engineer outcome, including incomplete attempts and intervention |
| 5 | When authorised teams and participants become available, run the [paired productivity study](../benchmarks/study_protocol.md) and register distinct team adoptions | External dependency; unscheduled | Only supported, reviewed aggregates and named approval authorities enter formal impact claims |

Do **not** make the absence of reviewers block further internal code quality work or the honest architecture presentation. Instead, mark the independent-outcome gates as pending. Avoid continuing to expand templates without a concrete usability defect or approved adopter request.

## Demo script for a technical decision-maker

For exact copy-and-paste PowerShell commands, see the [full AET end-to-end runbook](../END_TO_END_RUNBOOK.md). Its native Windows mock flows require no additional engineering work or independent reviewer and are explicitly labelled as author-operated acceptance, not adoption or measured time saved.

**Problem:** Repeat setup work and inconsistent starter engineering foundations across agent frameworks.

**Design:** A small Python CLI generates framework-native, independent projects with selectable provider configuration; no mandatory shared agent runtime.

**Show:** `agentkit list` -> `agentkit new demo-rag --template langgraph-rag --provider mock` -> `agentkit doctor demo-rag`; install and test the generated project, submit two local `/ask` requests separated by a synthetic corpus edit. Contrast with a Strands starter. Use the existing [fresh-user walkthrough](fresh-user-walkthrough.md) for exact commands.

**Evidence:** Four runnable starter types; 5/5 latest required CI checks, 92 configuration-environment checks, 2,864 synthetic adversarial events, 16 corpus-race trials and four mock Docker probes, with source-linked artefacts.

**Ask:** Review the architecture and decide whether it is acceptable as a *controlled, synthetic-only reusable starter candidate* and what conditions an approved pilot would require. This is **not** a request to accept unmeasured time savings or to certify the generated services for production.

## Safe statement for an evidence-based review

> Designed and implemented a local-first, cross-framework agent project scaffolder with four independently installable Python templates across LangGraph, Strands and LlamaIndex. Introduced template-aware Project Doctor, controlled provider configuration, atomic project publication, local API foundations, generated tests and Docker development examples. Verified the current release candidate through Windows/Linux Python 3.11/3.12 CI, comprehensive mock-mode combinations, adversarial and corpus-race testing, and a dated dependency audit. Prepared a reproducible independent adoption and matched-productivity study protocol; actual human productivity improvement and multi-team reuse remain to be validated.

**Decision record:** No stakeholder approval, independent human trial, production certification, measured labour saving or cross-team adoption is asserted here. Update the register only from new verifiable evidence.
