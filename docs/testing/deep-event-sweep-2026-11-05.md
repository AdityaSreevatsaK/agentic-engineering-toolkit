# Executed deep-event acceptance sweep, 5 November 2026

**Project:** Agentic Engineering Toolkit (AET) only. The separate AEA
project is untouched. The completed Deep Research review identified gaps in
adversarial-event, performance and runtime-security **evidence**, not a proven
remote exploit. This PR adds coverage rather than asserting production safety.

## Executed GitHub Actions evidence

- Repository: [AET](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit)
- [Full CI run 42041978382](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions/runs/42041978382)
- Tested PR branch head: `ff061982d4d7186c3966f20537eb9a357d031de7`.
  GitHub's PR merge-ref SHA for the actual CI checkout and evidence manifest
  is `e4e2bfb94b21bb746a29e2c56cbddaa30840c604`.
- **Five of five required jobs passed**: Ubuntu 24.04 and Windows 2025
  on Python 3.11/3.12, plus Ruff/focused mypy/Bandit quality.
- Existing full matrix passed **92/92 declared pairing checks**, plus
  **116/116 generation-negative checks** over the four platforms.
- New event matrix passed **2,864/2,864 deterministic scenarios**.
- All four deep-event artifact ZIPs were downloaded and independently
  SHA-256 checked against their embedded evidence manifests. All checksums
  matched; there were no failed scenarios.

| Platform | Supported pairs | Deep events passed | Result |
| --- | ---: | ---: | --- |
| Ubuntu 24.04, Python 3.11 | 23/23 | 716/716 | Pass |
| Ubuntu 24.04, Python 3.12 | 23/23 | 716/716 | Pass |
| Windows 2025, Python 3.11 | 23/23 | 716/716 | Pass |
| Windows 2025, Python 3.12 | 23/23 | 716/716 | Pass |
| **Total** | **92/92** | **2,864/2,864** | **Pass** |

### Event battery details

Each supported pairing executes 28 common scenarios: normal/repeated requests,
missing/null/type/empty/boundary/large inputs, malformed JSON/UTF-8, Unicode,
HTML/SQL/shell/prompt-injection-shaped inputs, synthetic secret-header canary,
controlled internal failure, route privacy and a bounded 8-request burst.
Each of the 12 RAG pairings additionally executes six corpus-change and
concurrent atomic-update scenarios. Apps run in isolated Python subprocesses,
with stripped environment credentials and `AET_PROVIDER=mock`, through actual
FastAPI TestClient/ASGI requests. No paid inference or public HTTP listener
is used.

## Observed performance evidence (advisory only)

The figures below aggregate **per-scenario** wall-clock duration samples,
including each bounded burst as one measured scenario. p50/p95/p99 were
computed from the corresponding archived JSON results, not invented.
Peak heap is the **largest tracemalloc-observed Python allocation** across
the 23 child interpreters in that environment; it excludes native library
memory and is not process RSS.

| Platform | Scenario p50 | p95 | p99 | Max traced heap |
| --- | ---: | ---: | ---: | ---: |
| Ubuntu, Python 3.11 | 10.37 ms | 82.65 ms | 188.16 ms | 21,881.5 KiB |
| Ubuntu, Python 3.12 | 10.35 ms | 81.91 ms | 189.71 ms | 21,860.7 KiB |
| Windows, Python 3.11 | 15.07 ms | 118.60 ms | 272.11 ms | 21,888.3 KiB |
| Windows, Python 3.12 | 8.73 ms | 69.19 ms | 156.51 ms | 21,865.9 KiB |

Hosted-runner variance makes these measurements diagnostic, **not**
validated production throughput or SLOs. The JSON and CSV artifacts also
retain per-pair elapsed time, CPU and burst throughput observations.

## Defect discovered and corrected by this sweep

The first Windows execution exposed a deterministic **test-writer portability
issue** while concurrently replacing local RAG corpus files: all 12 RAG
pairings failed the atomic-swap assertion, and several subsequent queries
did not see the expected final corpus. The corresponding HTTP reads returned
valid HTTP 200 responses. Evidence from that failed run
[42040732497](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions/runs/42040732497)
showed 698/716 events passed on Windows/Python 3.12.

The synthetic writer now retries only transient `PermissionError` sharing
violations for up to 30 bounded 10 ms delays before failing closed. The
reader-response, mutation and final cache-visibility assertions remain
strict. The corrected Windows run passed **716/716 in both Python versions**.
This confirms the harness can exercise Windows atomic file swaps reliably;
it does **not** establish fault-free arbitrary external corpus writers.

Two additional cross-platform test-correctness fixes were applied:
a byte-exact SHA-256 fixture that avoids Windows CRLF translation, and
acceptance of either HTTP 400 or 422 for invalid UTF-8 rejected by FastAPI.

## Supply-chain, security and retained evidence

All AET root and generated-project GitHub Actions versions for checkout v5,
setup-python v6 and upload-artifact v6 are pinned to **verified full SHAs**.
The separate cloud-extras advisory workflow now also runs on `v*` tag
pushes and includes the optional LlamaIndex Ollama dependency family.
No new dependency-CVE scan was executed in this PR, and tag pushes do not
block release creation: the owner still needs to review a successful
same-release advisory report.

Each of the four `deep-event-<os>-py<version>` bundles is retained for
90 days and includes `deep-event-results.json`,
`deep-event-metrics.csv`, `deep-event-failures.jsonl`,
`deep-event-security.json` and `deep-event-manifest.json`.
The manifest contains SHA-256 sizes/digests plus GitHub run/checkout SHA.
It is **not** a signed supply-chain attestation.

## Explicitly unverified

No live OpenAI/Azure/Anthropic/Bedrock or real Ollama inference, malicious
retrieved-document LLM red-team, sustained multi-process stress,
authentication/authorisation for production APIs, security penetration test,
real customer data, independently observed developer trial, multi-team
adoption or measured productivity gain is established by these tests.

**Outcome:** CI-backed, adversarially exercised local-first prototype suitable
for a controlled demonstration or pilot, **not** a production-certified
security platform.
