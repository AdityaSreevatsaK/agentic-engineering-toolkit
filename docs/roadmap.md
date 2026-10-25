# AET Scaffolder roadmap

The reusable asset is the **Agent Project Scaffolder**, not an evaluation framework. AEA remains a distinct project.

| Milestone | Outcome | Acceptance evidence |
| --- | --- | --- |
| M11: Product refocus | Scaffolder-only positioning, registry, template-aware Doctor, historical preservation | Existing commands and generated apps still pass; legacy Doctor fallback; four green CI jobs |
| M12: LangGraph RAG | Runnable generated RAG application with real indexing, retrieval and answer flow | Self-contained example, ingestion and query instructions, realistic local tests, generated-app CI |
| M13: AWS Strands | Runnable Strands-based agent application starter | Correct SDK integration with explicit offline/mock tests and documented real-service prerequisites |
| M14: Application foundations | Strengthen generated projects' config, structured logs, consistent errors, CI and deployment reference | Verified configuration failures, log hygiene tests, health/readiness boundaries, CI and deployment walkthrough |

## Work boundaries

**In scope:** project and source templates, sensible defaults, documentation, dependency packaging, application test scaffolds, developer-facing validation, reproducible generation, and deployability foundations.

**Out of scope:** AEA-style LLM evaluation pipelines, statistical significance testing, LLM-as-judge, advanced regression dashboards, quality-gate engines and fabricated benchmarking claims.

## Design constraints

- Keep the existing tool-agent template and old generated projects working.
- All milestones use feature branches and PRs, with four successful OS/Python CI combinations required before merge.
- Avoid mandatory paid model calls, cloud accounts or external credentials in normal CI.
- Templates must be **runnable implementations**, not empty folders or architectural sketches.
- Maintain provenance of M1-M10 without actively extending legacy evaluation packages.
- Keep the repository private; any use of employer/client material needs separate authorisation.

## Evidence for reuse

Passing tests establishes implementation integrity, not team adoption or saved engineering time. Future promotion evidence should distinguish verified code delivery, independent reproductions, authorised adoption and measured gains. Track each separately and do not infer later categories from earlier ones.
