# Security policy

AET is a reference scaffolder, not a security-certified production platform. The default local profile is unauthenticated and must not be exposed to the public internet. Generated apps now include an opt-in hardened profile, but it is not a production security certification.

## Reporting vulnerabilities

Please avoid disclosing exploitable vulnerabilities, credentials, tokens or sensitive data in public GitHub issues or pull requests. If GitHub's private vulnerability reporting is enabled for this repository, use its **Security** tab to submit a private report. Otherwise contact the repository maintainer through an existing private, authorised channel before publishing technical exploit details.

## Supported development

Security-related corrections should target the default `master` branch. Old generated application copies and historical feature branches are not maintained releases.

## Data handling

Never commit real secrets, client information, internal company assets or personal data. Tests use synthetic records or a restricted, publicly sourced evaluation subset. Actions logs and artifacts in public repositories are visible to others.

## Optional hardened application profile

Set `AET_SECURITY_MODE=hardened` and inject `AET_TENANT_KEYS_JSON` as a **process environment secret**, not a committed file. Its JSON object maps validated tenant identifiers to unique, random bearer tokens of at least 32 ASCII characters. Requests to `/invoke` and `/ask` require `Authorization: Bearer <token>`. RAG corpus files must be separately provisioned at `data/tenants/<tenant>/knowledge.jsonl` (or beneath the parent of the configured `AET_KNOWLEDGE_PATH`); missing tenant data fails closed. Configure `AET_TENANT_RATE_PER_MINUTE`, `AET_GLOBAL_RATE_PER_MINUTE`, `AET_MAX_CONCURRENT` and `AET_MAX_TENANT_CONCURRENT` to bound application requests.

These controls operate **per process**, not across workers or replicas. The deployment owner must still enforce TLS, trusted reverse-proxy configuration, distributed throttling, cloud-provider budgets, network policy, credential rotation, tenant authorisation and incident response. A loopback proxy may conceal the real client address, so never rely on the local-profile remote-client guard behind a proxy. For internet-facing traffic, use hardened mode plus a reviewed ingress and identity architecture.

`/ready` checks local configuration and RAG files only. It does **not** verify cloud-provider credentials or reachability; `/provider-status` explicitly reports `not_checked`. Model-generated answers and RAG passages remain untrusted. For details see [hardened profile guidance](docs/security/hardened-profile.md).
