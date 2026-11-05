# Bounded deep-event testing: scope and evidence

**Implementation status:** The test layer is committed on a feature branch
and must pass the five-check CI gate before being described as executed.

## Test contract

The runner `scripts/deep_event_matrix.py` enumerates the registry and creates
all **23 supported template/provider combinations** in isolated directories.
Each generated app is executed through FastAPI TestClient in a separate Python
interpreter with `AET_PROVIDER=mock` and cloud credentials removed from the
child process environment. No network server or billable model call is started.

Per pairing it executes **28 common scenarios**: health/readiness, repeated
requests, invalid/missing/null/wrong-type/empty inputs, boundary and 8 KiB,
64 KiB and 1 MiB payloads, malformed JSON/UTF-8, unknown fields, Unicode,
NUL, HTML/SQL/shell/prompt-injection-shaped strings, synthetic header canaries,
unknown route redaction, controlled exception sanitisation and an
eight-request concurrent burst. Each RAG pairing adds **six corpus-state
scenarios**: update, malformed records, duplicate IDs, restore, simultaneous
readers and atomic corpus updates, and final cache visibility.

Failures in these deterministic acceptance checks fail CI. All adverse
requests are synthetic and bounded. Unsafe payload strings are treated as
ordinary input data; passing mock-mode tests is **not proof of resistance to
prompt injection by a live LLM**.

## CI and evidence

The existing four smoke jobs (Ubuntu/Windows, Python 3.11/3.12) execute the
event sweep after the comprehensive provider matrix. The existing fifth
Ruff/mypy/Bandit job is unchanged. No job-status names change.

Each environment retains a `deep-event-<os>-py<version>` artifact for
90 days, containing:

| Output | Content |
| --- | --- |
| `deep-event-results.json` | All pair/scenario outcomes, event timing and Python heap metrics |
| `deep-event-metrics.csv` | Sanitised scenario latencies, statuses and process-wide CPU readings |
| `deep-event-failures.jsonl` | Only failing scenario IDs, status codes and stage identifiers |
| `deep-event-security.json` | Synthetic canary and controlled-exception outcomes |
| `deep-event-manifest.json` | SHA-256 digest and size of each file, with GitHub commit and run ID |

The digest file is **not** a signed supply-chain attestation. After the
verified run, a commit-pinned summary and run URLs can remain in version
control; CI raw artifacts expire.

Latency percentiles (p50/p95/p99), request throughput during the bounded
burst, elapsed time, process CPU and Python traced peak heap are advisory.
Measurements from GitHub-hosted runners are noisy and not application SLOs.
No arbitrary exceptions, secret values, request bodies, file paths or
tracebacks appear in the machine reports.

Reproduction, after installing development/SDK dependencies as in CI:

```powershell
python -m scripts.deep_event_matrix --json-out deep-event-results.json --csv-out deep-event-metrics.csv --failures-out deep-event-failures.jsonl --security-out deep-event-security.json
python -m scripts.evidence_manifest --out deep-event-manifest.json deep-event-results.json deep-event-metrics.csv deep-event-failures.jsonl deep-event-security.json
```

All output files must not already exist.

## Release advisory and immutable actions

The `dependency-vulnerability-audit` workflow runs monthly, manually,
and for `v*` tag pushes. It resolves each generated template's cloud extras,
plus the optional LlamaIndex Ollama extra, records installed versions,
runs `pip check` and evaluates current advisories with `pip-audit`.
**Tag creation is not blocked by these checks.** The release owner must
review successful same-commit advisory evidence before making a security
clearance claim. These four extras-family installs are not 23 separate
fresh virtual-environment installations.

All root and generated-app workflow GitHub Actions references are pinned
to verified **full commit SHAs**, with version comments retained.
Updates to those SHA pins require an explicit review.

## Known limitations

No real hosted model/Ollama inference, authentication, production deployment,
independent penetration test, long-duration/high-load capacity exercise,
complete client cancellation semantics, authenticated secrets, cloud billing,
human adoption or measured developer productivity is covered.

A clean offline pass means this is a **more extensively tested reusable
engineering prototype**, not a security-certified production platform.
