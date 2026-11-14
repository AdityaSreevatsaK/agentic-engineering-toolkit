# Independent AET hardening audit, 14 November 2026

> **Scope and evidence boundary:** This is an initial independently executed, narrowly scoped audit of **AET Agent Project Scaffolding** at baseline `e8fddbce1ee09ac6f3a17979a0ee26fa6ae12852`. It does **not** claim a new full independent 23-pair acceptance run or production security clearance. The separate AEA project was not accessed or modified. This report deliberately distinguishes new local execution from previously recorded GitHub Actions evidence.

## 1. Repository and environment

- Repository: `AdityaSreevatsaK/agentic-engineering-toolkit`, public, `master` at `e8fddbc` when inspected.
- The source of `src/aet_scaffolder/generator.py` was retrieved using the authorised GitHub integration. The isolated test copy was verified with `git hash-object`, which returned **`a6b5e2809287a77f1defc20c7316bc39eb85a68a`**, exactly matching the GitHub file-blob SHA at baseline.
- Independent execution host: Linux x86_64, kernel 6.18.57, CPython **3.13.5**. Separate virtual environment created using `python -m venv`; the only installed distribution was `pip==25.1.1`.
- Local narrow tests used only the standard library (`unittest`, `tempfile`, `pathlib`, `unittest.mock`). The **actual SHA-verified generator module** was tested against a minimal synthetic template and a small replacement registry. This is a module-level test, **not** an execution of the entire repository or any of the four real generated frameworks.
- The execution container could not resolve `github.com` through its shell, and had no Python 3.11, Python 3.12 or Docker executables. GitHub integration enabled source inspection and branch/PR operations but did not mount a complete checkout or supply a shell-capable connected runner.
- No credentials, customer data, cloud services, paid inference or publicly exposed FastAPI listeners were used.

## 2. Tests newly executed

The isolated **baseline** generator check reproduced a bug when a competing creator claimed a destination **after** the first existence test but **before** final publication. The original function completed successfully and replaced the competing empty directory on Linux.

The isolated **patched** generator passed **six out of six** standard-library checks:

| Check | Result | What it establishes |
| --- | --- | --- |
| Generate a synthetic mock project and manifest | PASS | The SHA-derived generator produces the expected basic output |
| Reject invalid directory traversal-shaped project name | PASS | A basic invalid-name input is rejected |
| Refuse an already populated destination | PASS | Ordinary no-overwrite contract still holds |
| Refuse a dangling destination symlink | PASS | New early symlink guard rejects the path |
| Reject a malformed Ollama model identifier | PASS | Existing option validation is preserved |
| Reject a competing empty directory created during staging | PASS | New pre-publication recheck detects the reproduced staging-time race |

The patched module was executed using `/mnt/data/aet-narrow/.venv/bin/python` with an isolated, synthetic source fixture. Tests took approximately **0.006 seconds**, which is not a meaningful AET generation benchmark. **Not executed locally:** the repository's pytest suite, real template generation, actual framework imports, packaging/wheel installation, Docker images, the 23-pair matrix, pip-audit or real HTTP application tests.

## 3. Previously verified CI, not rerun independently here

GitHub reported the latest pre-audit `master` workflow run [43238806437](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions/runs/43238806437), created **12 November 2026**, as **successful** for the baseline SHA. Its five jobs were:

- `quality (ruff, mypy, bandit)`
- `smoke (ubuntu-24.04, 3.11)`
- `smoke (ubuntu-24.04, 3.12)`
- `smoke (windows-2025, 3.11)`
- `smoke (windows-2025, 3.12)`

Prior recorded acceptance evidence includes [92/92 declared provider/template pairs and 116/116 generation-negative checks](comprehensive-matrix-2026-11-04.md) from 4 November 2026, and [2,864/2,864 bounded deep-event scenarios](deep-event-sweep-2026-11-05.md) from 5 November 2026. These are earlier **GitHub Actions** results, not independent tests run on 14 November. All cloud-selected projects in that provider matrix executed **mock** inference. There is no claim of real cloud SDK connectivity.

| Template | Declared configurations | Fresh independent installation this audit | Existing recorded mock matrix |
| --- | ---: | --- | --- |
| `tool-agent` | 6 | Blocked | 6 per CI platform |
| `langgraph-rag` | 6 | Blocked | 6 per CI platform |
| `strands-agent` | 5 | Blocked | 5 per CI platform |
| `llamaindex-rag` | 6 | Blocked | 6 per CI platform |
| **Total** | **23** | **0 freshly installed** | **23 per CI platform** |

## 4. Findings, classification and dispositions

### AET-2026-11-14-01, Medium: destination-claim race in generator

**Verified:** In the baseline implementation, `generator.generate()` calls `target.exists()` before copying the template into a staging directory, then calls `staging.rename(target)`. A deterministic local test used a mocked `_copy_template()` to create an empty `target` directory *after* the initial check. On Linux, the original `rename` replaced this directory and generation returned success.

**Impact:** A concurrent local process can lose an **empty** directory created during scaffolding. Normal existing populated project directories are rejected; this is not a demonstrated overwrite of populated projects, a remote exploit, or an exposure of secrets. The preconditions make it a constrained local race.

**Mitigation in this PR:** Detect both existing paths and dangling symlinks up front; check again after all staging work and before the rename; add deterministic regression tests for both situations. The patched staged-claim reproduction passed locally.

**Residual risk:** The final `exists()` check and `rename()` are not an indivisible no-replace operation. An appropriately timed concurrent creator could still win the final micro-window on platforms where rename replaces empty directories. **This is a partial mitigation, not a complete race elimination.** A fully atomic, cross-platform no-replace publication mechanism needs separate design review: platform-specific exclusive rename offers stronger atomicity but increases portability complexity; an exclusive `mkdir`/copy publication is portable but exposes incomplete projects and changes crash semantics. Do not claim this is fully resolved.

### AET-2026-11-14-02, Low: `agentkit list` obscures unsupported provider pairs

**Verified by source inspection:** The old command printed every template name followed by the **union** of available providers, without showing which provider was supported by which template. In particular, `strands-agent` intentionally does not support Ollama. A user seeing the global Ollama listing could incorrectly expect Strands/Ollama to work.

**Fix in this PR:** Print an explicit `Supported providers` line beneath each template while preserving the existing global `Providers:` line for backwards compatibility. Add an exact registry-driven CLI output test. Validation of this change awaits the PR's actual CI run.

### AET-2026-11-14-03, Improvement: duplicated pilot-analysis pytest step

**Verified by workflow inspection:** The CI smoke job runs `python -m pytest tests -q` and later reruns `tests/test_pilot_analysis.py` separately. The latter is already collected by the former.

**Change in this PR:** Remove only the redundant second invocation. All four smoke jobs, the independent quality check, historical tests, and their existing status-check names remain. Any speed improvement has **not** been measured.

### Non-finding: dangling symlink replacement

The baseline Linux test showed that `Path.exists()` returns false for a dangling symlink, but a directory rename onto that link failed with `ENOTDIR` and did **not** replace it. This is **not** evidence of prior destructive symlink overwriting. The new explicit guard improves predictability and error reporting.

## 5. Security, deployment and dependency boundaries

- The generated APIs are unauthenticated local reference applications. This is an **intentional documented limitation**, not a newly reproduced vulnerability. They must not be exposed on a public interface without a separate security design.
- The inspected generated HTTP middleware uses server-created request IDs, generic 500 bodies and sanitised request logging. No new independent ASGI or penetration-testing claim is made from reading this code.
- Both RAG templates use bounded local JSONL inputs. Existing instructions marking retrieved text as untrusted do not establish resistance to a live LLM prompt-injection attempt.
- No new `pip check`, `pip-audit`, optional cloud-extras resolution, lockfile audit, image build, SBOM or vulnerability-cleared claim was possible in the isolated execution environment. The repository retains its separate scheduled/manual advisory workflow.
- The root workflow uses existing action SHA pins and five required check names. Only a redundant test command is removed.

## 6. Performance and reliability

No real full-template startup timing, request-latency percentile, memory/RSS profile, Docker image timing or sustained-load test was newly executed. The prior deep-event report contains advisory hosted-runner measurements and must not be treated as production SLO evidence. The synthetic one-file generator run in this audit is deliberately excluded from performance comparisons.

## 7. Prioritised next verification gates

1. **Before merging:** complete all five final-head PR checks, examine failures, verify the new unit tests on Windows and Linux, and preserve the branch ruleset.
2. **Highest correctness priority:** make destination publication truly no-replace across supported platforms without silently sacrificing atomic publication. Keep the residual race documented until then.
3. Obtain a shell-accessible full checkout with independent Python 3.11 and 3.12 environments; build the real wheel, generate all 23 pairs, isolate each generated app's environment, run pytest and ASGI probes, and capture exact dependency versions.
4. Build and smoke-test the **three additional** generated container images; existing prior CI covered only `tool-agent`.
5. Run a fresh same-SHA cloud-extras dependency advisory scan, and measure a clean four-template onboarding trial. Record independent engineers' observations separately from machine tests.
6. Consider CI restructuring only after measuring duplicated dependency installs and wall-clock timing. Do not split historical coverage or change the five required status checks without an explicitly planned ruleset migration.

## 8. Change and review status

The changes are proposed on branch `audit/independent-hardening-2026-11-14`. PR and final-head CI details must be appended **only after observed execution**. This document is evidence of narrow independent checks plus pre-existing CI inspection, **not** a completed comprehensive independent hardening certification.
