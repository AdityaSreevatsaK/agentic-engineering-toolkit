# M19 evidence and release gate

The goal is **pilot-readiness**, not declaring production readiness or
claiming developer-time savings.

See the [5 November deep-audit remediation register](../testing/post-audit-remediation-2026-11-05.md) for fixed correctness findings, pre-existing provider transport controls, reproducible regression tests, and explicitly unverified gates. A separate optional GitHub Actions dependency-vulnerability workflow audits installed package resolutions; no advisory-scan success is claimed before a real run.

On 4 November 2026, the [comprehensive supported-combination report](../testing/comprehensive-matrix-2026-11-04.md)
recorded 92/92 supported offline pair checks, 116/116 negative checks,
all four Windows/Linux CI jobs and the dedicated quality gate passing on
PR #29 run 41781179570. Cloud models were not invoked. Complete/check each gate only with evidence
from its actual execution; this file contains no fabricated outcomes.

| Gate | Acceptance requirement | Evidence | State in repository |
| --- | --- | --- | --- |
| Code and packaging | Four templates in one installable AET wheel; old generated projects remain valid | Unit tests, Doctor, package tests | Automated test coverage available |
| Static quality | Ruff, focused mypy and Bandit checks succeed on the reviewed commit | Dedicated `quality` CI job | Passed in post-merge master run 41782430839 |
| Provider policy | Bedrock and Strands transport timeout/retry parameters forwarded in offline constructor contracts | Generated unit tests and provider parity test | Constructor double regression tests passed in PR #29; paid inference remains unverified |
| Reproducibility | Pin CI runner images, record installed versions, require dependency consistency | GitHub Actions `ci-resolved` artifacts and `python -m pip check` | Tested dependency sets with version evidence, not a platform-specific lockfile |
| Functional smoke | Four generated mock apps pass health/readiness, request handling and invalid-input checks; both RAG variants reflect corpus change | `scripts/release_smoke.py` per-platform JSON | All four platform jobs passed in post-merge master run 41782430839, including the M19 smoke |
| Compatibility | All four Windows/Linux Python 3.11/3.12 jobs successful on final integrated commit | GitHub Actions matrix | All four matrix jobs passed in post-merge master run 41782430839 |
| Optional public-data evaluation | External NYC 311 API must not block required CI | [Manual-only workflow](../../.github/workflows/nyc311-live.yml); synthetic fixture in required CI | Manual run available after merge; not a release gate | 
| LlamaIndex provider timeouts | Validated timeout forwarded to all native provider constructors | Generated provider tests with injected SDK doubles | Regression coverage added; live provider operation unverified | 
| Independent usability | At least one authorised non-author engineer independently performs the primary two-request corpus trial | Private completed observer notes | **Not collected** |
| Developer-time improvement | Balanced manual-vs-AET matched baseline with explicit active/wait time | [M4 protocol](../benchmarks/study_protocol.md) | **Not measured** |
| Multi-team adoption | Independent confirmed use by more than one authorised delivery team | Approved adopter/project evidence | **Not verified** |
| Production suitability | Security, identity/ACL, operational controls, cloud provider validation | Client-specific architecture review and tests | **Out of scope / not verified** |
| Governance | PR/CI ruleset active for `master` | [Owner setup steps](../governance/master-branch-protection.md) and [Issue #13](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/issues/13) | **Unprotected on 4 November 2026; an authenticated owner must run the supplied setup command or use Settings** |

A passing pipeline permits describing AET as a **CI-verified local-first
scaffolder and controlled pilot candidate**. It does not satisfy the remaining
human adoption, productivity, security, governance or employer-approval gates.
Completed reviewer notes must remain outside this public repository. As of 4 November 2026 before the owner applies branch protection, GitHub reported `master` as unprotected and no repository rulesets. The version-controlled helper `scripts/configure_branch_ruleset.py` is dry-run by default; its existence does **not** activate ruleset enforcement.

**Minimum next action for the owner:** Confirm organisation/IP permission and
the GitHub ruleset. Offer the synthetic-data reviewer protocol to an
authorised unfamiliar engineer when available. Record only real outcomes.
