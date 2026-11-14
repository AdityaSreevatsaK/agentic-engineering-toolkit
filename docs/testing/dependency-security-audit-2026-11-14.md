# Resolved dependency security audit, 14 November 2026

**Project:** AET Agent Project Scaffolder only. **Evidence:** [GitHub Actions run 43587431451](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions/runs/43587431451), opened from [PR #39](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/pull/39). **PR source SHA:** `b23fd8ca74cc0362cf70b4bf54224d328174fad9`. All four `resolved-dependency-audit` jobs passed on Ubuntu 24.04, Python 3.12. This is a time-specific third-party package advisory result, **not** an AET security certification.

## Actually executed

The existing `.github/workflows/dependency-audit.yml` generated one mock AET project for each of four registered templates. Each isolated CI matrix environment installed the AET scaffolder, `pip-audit`, the generated project's `[dev,cloud]` extras and, for LlamaIndex, its separate `[ollama]` extra. It then ran `pip check`, saved `pip freeze --all`, and ran `python -m pip_audit --format json --output dependency-audit.json`. No paid inference, model credentials, real data or public application endpoint was used.

The four machine-produced GitHub Actions artifact ZIPs were downloaded and their `dependency-audit.json` and `resolved-versions.txt` files parsed separately. The following **counts come from the actual JSON evidence**, not estimates:

| Template | JSON dependency entries | Third-party entries audited | Local packages skipped | Reported vulnerabilities | `pip check` |
| --- | ---: | ---: | ---: | ---: | --- |
| `tool-agent` | 89 | 87 | 2 | 0 | PASS |
| `langgraph-rag` | 89 | 87 | 2 | 0 | PASS |
| `strands-agent` | 86 | 84 | 2 | 0 | PASS |
| `llamaindex-rag` | 125 | 123 | 2 | 0 | PASS |
| **Total environment-specific checks** | **389** | **381** | **8** | **0** | **4/4 PASS** |

**Counting limitation:** The 381 third-party entries include repeated dependencies across independently resolved environments; they are *not* 381 distinct package names. Every audit JSON lists two explicit `skip_reason` records, for `aet-scaffolder` and `audit-app`, because these local source distributions are not hosted on PyPI. The audit is not a source-code vulnerability scan of those packages; AET's existing code tests and reviews serve a different purpose.

## Evidence access

The CI artifacts contain the exact resolved package versions and the JSON advisory records, with the following GitHub artifact IDs. Retention is 30 days, so the human-readable summary here remains useful after expiry.

| Template | Artifact ID | Contents |
| --- | ---: | --- |
| `tool-agent` | `14109999557` | `dependency-audit.json`, `resolved-versions.txt` |
| `langgraph-rag` | `14111375056` | same |
| `strands-agent` | `14111025890` | same |
| `llamaindex-rag` | `14110724429` | same |

No action was taken to upgrade packages: the observed third-party resolutions passed the advisory and dependency-consistency checks. A clean result only means **no advisories reported by the queried audit service for these installed package versions at the audit time**. It is not a guarantee against future disclosures, unreported vulnerabilities, private advisories, credential leaks, or application-layer security defects.

## PR-trigger hardening

PR #39 extends the **existing** dependency audit workflow, without creating a new workflow, to run when a PR into `master` changes its workflow definition, root `pyproject.toml`, or any generated template `pyproject.toml`. The prior manual, monthly and `v*` tag triggers remain. The audit is *not* one of the five mandatory CI check names; CI's existing branch-protection contract remains unchanged. Network access is used only for package resolution and advisory lookup.

## Residual verification gates

1. Review an updated audit when the dependency graph changes or before a release. The tags trigger a scan **after** tag creation, not a release blocker.
2. The `[cloud]` extras audit one *combined* dependency resolution per template, plus the separate LlamaIndex Ollama extra. It does not independently install every one of the 23 template/provider combinations with individual extras.
3. Recheck Windows-specific wheels and platform-conditioned dependencies if Windows security assurance is required: this advisory run covers Linux Python 3.12 only. The main five-check CI separately covers Windows and Linux Python 3.11/3.12.
4. Keep vulnerabilities, CVE remediations and general application-security findings separate: passing `pip-audit` cannot certify the unauthenticated generated APIs for public deployment.
5. Verify the five required PR checks on the **final documentation head** and the post-merge `master` commit. No claim of merge or post-merge success is made within this scan evidence.
