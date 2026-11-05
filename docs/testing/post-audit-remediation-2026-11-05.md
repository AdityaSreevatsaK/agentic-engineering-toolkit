# AET post-deep-audit remediation register (5 November 2026)

**Scope:** Agentic Engineering Toolkit (AET) only. The separate AEA project is
not modified. This register tracks the actual findings reported in the latest
deep research audit. It does not claim full penetration testing or production
certification.

## Confirmed existing remediations (before this change)

The audit's discussion of **SEC-01 (LangChain Bedrock timeout/retry)** and
**SEC-02 (Strands transport controls)** reflected an older view of the code:
both LangChain templates already pass `timeout` and `max_retries` to native
`ChatBedrock`, and Strands models already configure OpenAI, Anthropic, Azure
and botocore transport bounds. **BUG-04 (LlamaIndex cloud timeout wiring)**
was likewise already implemented. These have offline constructor and
regression tests, not approved live provider inference. Do not reopen
implemented fixes without a concrete failing reproduction.

## Remediation in this PR

| Audit ID | Treatment | Evidence and caveat |
| --- | --- | --- |
| BUG-01 | Fixed: all supported templates have complete registry-driven Doctor settings coverage, including Azure endpoints/versions, provider models, timeout/retries and retrieval settings | New field-contract tests remove each supported key and confirm Doctor rejects it; pre-M17 Strands layouts retain backwards compatibility |
| BUG-02 | Fixed: generic, accurate cloud readiness message in Strands | Parameterised offline readiness tests across all hosted modes |
| BUG-03 | Fixed: Doctor now uses standard PEP 508 parsing and canonical package names, including markers and extras | New validator tests reject invalid/inactive declarations |
| SEC-04 | Regression coverage added: both RAG prompt paths explicitly label retrieved content untrusted | Offline spies test prompt construction; **prompt injection resistance is not guaranteed** |
| BUG-05 | Improved privacy-safe observability: request logs record only exception class for unhandled failures and treat HTTP 5xx as failure | All four generated templates still hide exception message, traceback, query data and secrets |
| PERF-01 | Bounded in-process caching: unchanged JSONL snapshots avoid repeated parses, LangGraph BM25 reuses token counters, and LlamaIndex keyword indexes are reused | Cache keys include source content for search/index and file metadata for snapshots; corpus updates are still checked by the full offline API smoke and new mutation tests |
| SEC-03 | Added manual/monthly resolved-dependency advisory scan across all four templates, including optional cloud SDK dependencies | Each template is audited in a separate CI environment, with exact resolution artifacts and non-zero failure when vulnerabilities are found; broad ranges remain and **no scan result is claimed until the workflow actually runs** |

## Explicitly deferred / limits

- Historical M7-M10 validation still runs in required PR CI. Splitting it into a
  slower compatibility workflow is a **CI-maintenance trade-off**, not a
  correctness fix; the full validation and five checks are deliberately
  retained for the current leadership gate.
- Self-contained templates necessarily duplicate some foundation and provider
  code so generated applications need no AET runtime dependency; parity and
  per-template regression tests guard against drift. A wholesale abstraction
  rewrite would undermine that contract.
- A tag-pinned Python base image remains acceptable for **development-only**
  example containers. Production release images should use reviewed,
  digest-pinned builds and independent image vulnerability scans.
- Prompt instructions do not make untrusted corpora safe. The generated local
  FastAPI services lack authentication by design and must not be publicly
  exposed without a separate production security design.
- No live OpenAI, Azure, Anthropic, AWS Bedrock, Ollama model, independent
  developer trial, multi-team adoption or actual time saved is verified here.
- Repository branch protection requires a separate owner-authenticated GitHub
  ruleset action, documented in `docs/governance/master-branch-protection.md`.

**Release claim:** CI-validated local agent scaffolder and controlled-pilot
candidate, not a production platform or quantified business intervention.
