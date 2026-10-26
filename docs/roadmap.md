# AET Scaffolder roadmap

The reusable asset is the **Agent Project Scaffolder**, not an evaluation framework. AEA remains a distinct project.

| Milestone | Outcome | Acceptance evidence |
| --- | --- | --- |
| M11: Product refocus | Scaffolder-only positioning, registry, template-aware Doctor, historical preservation | Existing commands and generated apps still pass; legacy Doctor fallback; four green CI jobs |
| M12: LangGraph RAG | Runnable LangGraph application with bounded JSONL ingestion, BM25 lexical retrieval and evidence-based answers | Self-contained sample corpus, local ingestion and query instructions, offline mock tests, fake Ollama tests and generated-app CI |
| M13: AWS Strands | Runnable SDK Agent and annotated tool, deterministic offline Strands event model and opt-in Bedrock mode | Offline real-SDK tool invocation, fake Bedrock construction, generated API tests and four-platform CI |
| M14: Application foundations | Add configuration validation, sanitised JSON request logs, request IDs, honest readiness, generated CI and non-root container reference to all three templates | Generated tests, Doctor and wheel packaging on four OS/Python jobs, plus Docker build smoke |
| M15: Adoption validation | Prepare an independent hand-off, actual HTTP/corpus-change exercise, privacy-safe reviewer notes and reusable machine preflight | Four-platform preflight CI, accepted protocol and documentation; **external participant results remain pending** |

## M15 pilot result boundary

The M15 pilot kit is [documented](adoption/README.md) and can be exercised entirely offline, but **independent engineer validation cannot be checked in by the AET author**. The owner must invite real reviewers (with appropriate authorisation) to gather actual outcomes. Existing M4/M8 matched-trial protocols remain the only basis for future developer-time claims. There is no fourth template planned until observed adoption problems justify it.

## Work boundaries

**In scope:** project and source templates, sensible defaults, documentation, dependency packaging, application test scaffolds, developer-facing validation, reproducible generation, and deployability foundations.

**Out of scope:** AEA-style LLM evaluation pipelines, statistical significance testing, LLM-as-judge, advanced regression dashboards, quality-gate engines and fabricated benchmarking claims.

## Design constraints

- Keep the existing tool-agent template and old generated projects working.
- All milestones use feature branches and PRs, with four successful OS/Python CI combinations required before merge.
- Avoid mandatory paid model calls, cloud accounts or external credentials in normal CI.
- Templates must be **runnable implementations**, not empty folders or architectural sketches.
- Maintain provenance of M1-M10 without actively extending legacy evaluation packages.
- Keep the repository public only with reviewed material; employer/client information still requires separate authorisation.

## Evidence for reuse

Passing tests establishes implementation integrity, not team adoption or saved engineering time. Future promotion evidence should distinguish verified code delivery, independent reproductions, authorised adoption and measured gains. Track each separately and do not infer later categories from earlier ones.
