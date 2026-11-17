# Source-checked follow-up to the 17 November 2026 audit

The supplied five-page audit explicitly states **no actual source-code review was possible** (page 5). Its critical/high labels therefore describe potential risks, not reproduced defects. We reviewed the code at master `a41d3284878e` before making changes.

| Report concern | Observed implementation and action |
| --- | --- |
| Critical multi-tenant leakage | Hardened mode already authenticates separate tenant tokens and resolves tenant-specific corpus paths; both RAG templates test cross-tenant denial. No cross-tenant leak was reproduced |
| Query abuse/prompt injection | Both RAG starters use bounded lexical retrieval, source IDs and untrusted-evidence framing; synthetic adversarial tests exist. This change adds Unicode query normalisation, control-character rejection and unknown-field denial. Normalisation alone does not prevent indirect prompt injection |
| Request limits | Hardened profile already has tested per-tenant/global minute, daily and concurrency limits, but they are process-local. Gateway quotas and paid-provider budgets remain external |
| Dependencies and supply chain | The repository has dependency audit/lock and digest-pinned deployment paths, SHA-pinned GitHub Actions, and secret scans; PR #56 fixed scanner-version alignment. The audit demonstrated no specific vulnerable package or CVE |
| Observability/fail-safes | Existing foundations emit sanitised JSON request IDs, routes, status and duration without raw prompts, secrets or SDK exception strings. This change rejects blank and oversized Ollama responses. Central alerts and live-provider response validation remain unverified |
| Testing and documentation | Already includes auth, tenant-isolation, rate-limit, Windows/Linux and malicious-document tests. New tests cover duplicate auth headers, request validation and malformed Ollama output. This document distinguishes completed code controls from external deployment work |

## Still required outside this repository

- Verified TLS and trusted ingress; restricted health/readiness diagnostics; body size and distributed rate limits; least-privilege IAM; private secrets and egress policies
- Approved live provider tests and budget ceilings, with proof of provider failures/retries and model-level adversarial behaviour
- Monitoring, alerting, retention and incident runbooks exercised against a target deployment
- Deployment-specific concurrency/load evidence and regulated-data retention/deletion controls, when applicable
- Independent pilot/adoption and developer productivity evidence

Track external readiness separately in [issue #50](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/issues/50). Green mock tests must not be presented as production certification.
