# Historical AET assets (M1-M10)

This document retains navigable links to earlier work after M11 refocuses the **active** AET product on Agent Project Scaffolding.

| Asset | Existing location | Status after M11 |
| --- | --- | --- |
| Agent Quality Kit | packages/agent-quality-kit/ | Legacy standalone code; preserved with tests |
| Portable Provider Contract | packages/agent-provider-contract/ | Legacy reference contract and compatibility bridge; preserved with tests |
| Three-asset acceptance demo | scripts/run_demo.py, docs/demo/ | Historical integration demo; regression coverage retained |
| Pilot/study tools | scripts/analyze_pilot.py, docs/pilot/, docs/benchmarks/ | Historical protocols and evidence register; no adoption claims |
| Public-data evaluation | scripts/evaluate_olist.py, scripts/evaluate_nyc311.py, docs/evaluation/ | Historical experiments and results; not AET's active product |
| Provider portability architecture | docs/architecture/provider-portability.md | Reference proposal; does not establish deployed cloud adapters |
| Architectural decisions | docs/decisions/0001 through 0010 | Immutable engineering decision history |

The corresponding test suites and four-platform CI matrix remain to catch regressions. This does **not** imply a commitment to expand these products or the evaluation pipeline. Historical commands and package installations remain available to existing users.

## AEA boundary

The separate Agent Engineering Accelerator owns agent-level evaluation, regression testing, statistical analysis, LLM judging and CI quality gates. An optional future integration might add installation guidance or configuration hooks to scaffolded projects, but it will not reimplement AEA and is deferred until its source repository and contracts are available.

## Integrity of historical evidence

Earlier NYC 311 testing establishes public-data-backed deterministic status-routing integration, not model intelligence or developer productivity. The M8 pilot/evidence register explicitly distinguishes tested engineering output from uncollected adoption and productivity results.

Historical documentation refers to the repository's earlier private status. The repository is now public; this change does not authorise sharing participant-level results or employer/client information without permission.
