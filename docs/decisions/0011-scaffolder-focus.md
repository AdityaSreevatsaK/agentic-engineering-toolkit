# ADR-0011: Focus AET on agent project scaffolding

**Status:** Accepted as M11 engineering direction
**Date:** 25 October 2026

## Context

M1-M10 produced three packages and substantial demonstration/evaluation work. A separate Agent Engineering Accelerator (AEA) project already owns more comprehensive agent evaluation, statistical analysis, LLM judging and CI quality gates. Continuing to expand these capabilities in AET would duplicate maintenance and blur the reusable asset's purpose.

The current scaffolder supports one FastAPI/LangGraph template but its CLI, generator and Doctor hardcode tool-agent assumptions. Future LangGraph RAG and AWS Strands templates require a small, explicit extension point.

## Decision

1. The **Agent Project Scaffolder** becomes AET's only active product. Its remit is creating runnable, maintainable application starting points, not certifying agent quality.
2. Add one declarative registry that names bundled templates and describes supported providers, required files, dependencies and sample settings.
3. New generated projects include a bounded, non-secret .aet-template.json manifest with a schema version and template identifier. Doctor uses the manifest to select a validation profile. Pre-M11 projects lacking the manifest retain the original tool-agent checks.
4. Keep existing package distribution name, CLI commands and defaults, synthetic workflow behaviour and generated API contract.
5. Retain historical packages, tests, documentation, pilots and evaluation results in place; mark them as legacy rather than delete, relocate or recreate them.
6. Preserve the four-job CI matrix. Legacy checks remain regression coverage for existing assets, not a signal to expand AET's evaluation product scope.
7. Defer optional AEA integration until the separate AEA repository and stable integration interface exist. Do not add a mandatory AEA dependency.

## Consequences

- Future templates can declare their contents and Doctor checks centrally, reducing change risk when extending generation.
- The manifest is metadata, **not** a security attestation, production-readiness certificate or licence.
- Unknown or malformed manifests fail Doctor rather than silently falling back to the legacy profile.
- CLI provider flags still describe the existing tool-agent capabilities; later templates may require template-specific CLI options and their own tested provider support.
- No claims of actual cloud deployment, independent developer adoption, time saved or LLM reasoning are justified by M11.
- Provider Contract and Agent Quality Kit source code remains intact for historical reproducibility; they are not new AET roadmap work.

## Rejected alternatives

- **Delete old packages or evaluation scripts:** destructive and unnecessary; sacrifices reproducibility.
- **Turn AET into a combined scaffolding/evaluation platform:** duplicates AEA and weakens clarity.
- **Rebuild the scaffolder from scratch:** creates avoidable compatibility and regression risk.
- **Require AEA for generated projects now:** its separate repository/interface has not been established.
