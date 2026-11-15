# Hardened deployment profile (opt-in)

**Default:** local/reference. **Alternative:** `AET_SECURITY_MODE=hardened` with explicitly provisioned tenant credentials. This profile is a security extension, not production certification.

## Required operator setup

1. Generate independent random bearer tokens with at least 32 ASCII characters and store them in a secret manager. Inject `AET_TENANT_KEYS_JSON` as a process environment variable, e.g. a JSON mapping from tenant ID to token. Never commit or print tokens, or put them in `.env`.
2. Set `AET_SECURITY_MODE=hardened`. Every `POST /invoke` and `POST /ask` requires a matching `Authorization: Bearer <token>` header. No token or an invalid token returns 401. Invalid server-side key configuration returns 503.
3. For RAG, provision one corpus per tenant under `data/tenants/<tenant>/knowledge.jsonl`. If `AET_KNOWLEDGE_PATH` is changed, the `tenants` directory is created beneath that file's parent. Tenant IDs are validated; symlinks and paths escaping the tenant root are rejected. Missing tenant corpus returns 503, never shared documents.
4. Configure `AET_TENANT_RATE_PER_MINUTE` (default 30), `AET_GLOBAL_RATE_PER_MINUTE` (300), `AET_MAX_CONCURRENT` (20), `AET_MAX_TENANT_CONCURRENT` (5). Add `AET_TENANT_DAILY_REQUEST_LIMIT` (default 100) and `AET_GLOBAL_DAILY_REQUEST_LIMIT` (1000) to cap request attempts during any rolling 24-hour period. These limits are process-local and return 429 when exceeded.
5. Put the service behind a reviewed TLS ingress with trusted proxy configuration, a distributed gateway rate limiter, network egress restrictions, cloud-provider quotas/billing alerts, secret rotation and operational monitoring. Do not use the local-profile IP guard as a substitute for these controls.

## Health and diagnostics

`GET /health` is liveness. `GET /ready` validates local configuration and, for RAG, the tenant corpora. A 200 response does **not** mean the cloud provider can be reached. `GET /provider-status` reports `{"provider":"...","connectivity":"not_checked"}`; it makes no paid inference request. Provider availability requires separately authorised tests.

Request logs contain server-generated IDs, fixed route names, status and duration, but no bodies, credentials, exception messages or arbitrary paths. Set `AET_OPERATOR_STACK_FRAMES=1` only on a protected operator log channel to include sanitised frame metadata without SDK exception messages.

## Limits and threat model

- Bearer keys are a simple tenant authentication boundary, not an SSO or fine-grained authorisation system. Do not assign one key to multiple tenants.
- Per-process request counters (including daily ceilings) are **not** distributed quotas, cost budgets or token-based limits. They reset on process restart. Enforce monetary budgets and provider-side quotas outside AET. Use a central gateway and provider-side quotas for multi-worker or multi-replica deployments.
- Local-profile remote-client rejection is based on the ASGI peer address. A reverse proxy can make remote callers appear local. Never expose live inference through an untrusted loopback proxy.
- Retrieved text remains untrusted, including fake system prompts and exfiltration instructions. These starters do not give retrieved text privileged tools, but cannot guarantee model compliance. Human review and model-level adversarial testing remain necessary.
- Use immutable dependency locks and digest-pinned production images before deploying. The default Dockerfile remains a localhost development reference.
