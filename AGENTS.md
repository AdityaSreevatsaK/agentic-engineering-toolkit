# AET: guidance for repository-aware coding agents

**Start here:** [PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md) is the comprehensive, source-grounded architecture and maintenance reference. It covers product objectives, the entire repository structure, four generated applications, 23 declared template/provider configurations, the CLI/generator/Doctor, framework-native model integrations, API contracts, RAG corpus rules, caching, security, CI evidence, extension procedures, limitations and troubleshooting. **Read the relevant sections before changing code.** The running source code and tests take precedence over explanatory prose.

## Project identity

- **Product:** Agentic Engineering Toolkit, presently focused on *Agent Project Scaffolding*, not an agent-evaluation platform.
- **CLI:** `agentkit list`, `agentkit new`, `agentkit doctor`; Python 3.11+.
- **Templates:** `tool-agent`, `langgraph-rag`, `strands-agent`, `llamaindex-rag`. Choose only supported provider combinations from `src/aet_scaffolder/registry.py`.
- **Default:** deterministic local `mock`. Do not introduce paid inference, credentials, network requirements or real customer records into CI.
- **Generated applications:** each is a self-contained, independently installable Python project. AET must not become a required shared runtime dependency.
- **Separate project:** Agent Engineering Accelerator (AEA) owns agent evaluation, statistical regression and LLM judging. Keep AET's focus separate.
- **Status:** CI-verified offline engineering prototype and controlled-pilot candidate, not a security-certified production platform. No independently measured productivity savings or multi-team adoption claims.

## Contribution protocol

1. Inspect the latest `master`, relevant files, open PRs/issues and accepted ADRs. Check the [deep dive](PROJECT_DEEP_DIVE.md) for architecture and source pointers.
2. Make narrowly scoped changes on a feature branch and PR. The protected `master` requires **five** CI checks (Ubuntu/Windows × Python 3.11/3.12, plus Ruff/mypy/Bandit quality) and resolved conversations.
3. Preserve the legacy `agentkit` contract, manifest-less pre-M11 Project Doctor support, generated API schemas, safe names, no-overwrite semantics and bundled wheel templates.
   - Project publication must stay atomic and non-replacing: Linux uses `renameat2(RENAME_NOREPLACE)`, Windows uses non-replacing rename; fail closed on unsupported local filesystems rather than using a racy fallback.
4. For template changes, update the declarative registry, emitted files, Docker/CI/docs as applicable, generated tests and root regression tests. All templates should work with mock inference without secrets.
5. For provider changes, use framework-native SDK integrations, optional dependency extras, safe environment configuration and injected fake-SDK tests. **No live billable model calls in automated CI.**
6. Protect privacy: no secrets/client data in code, PRs or Actions artifacts; no raw prompts/answers/exception messages in request logs; no unauthenticated public API deployment.
7. Verify real results before reporting success. Distinguish generation, Doctor, SDK fakes, mock ASGI tests, actual live inference, independent trials and production security.
   - Four-image Docker smoke runs only in the existing Ubuntu/Python 3.11 CI job. Bind containers to loopback; verify both actual HTTP mock probes and the recorded evidence before claiming Docker coverage.
   - All four Windows/Linux Python 3.11/3.12 CI jobs install each generated template in a **fresh separate virtualenv**, run per-app pytest and mock ASGI probes, verify `pip check`, and retain dependency resolutions. For local diagnostics, run sequentially with `python -m scripts.isolated_install_smoke --json-out isolated-installations.json --versions-dir isolated-resolved`; CI adds `--jobs 2` for bounded parallelism while keeping each installation and probe intact. See [CI timing investigation](docs/testing/ci-efficiency-2026-11-14.md).
   - Changes to root/generated dependency manifests or the dependency-audit workflow also trigger the existing online advisory audit on PRs. Review its JSON and `pip freeze` evidence: editable local AET packages are explicitly skipped by PyPI advisory lookups. See [14 November 2026 audit](docs/testing/dependency-security-audit-2026-11-14.md).
8. Merge only after final-head checks pass. Do not bypass or weaken branch protection, silently delete historical work or mix changes with AEA.

## Source map

- Generator / manifest / contracts: `src/aet_scaffolder/{cli,generator,registry,validator}.py`.
- Generated template code: `src/aet_scaffolder/templates/`.
- Root and per-template tests: `tests/` and each template's `tests/`.
- Root CI: `.github/workflows/ci.yml`. Dependency audit: `.github/workflows/dependency-audit.yml`.
- Detailed test/evidence limitations: `docs/testing/` and `docs/release/`.
- Product boundary: `docs/decisions/0011-scaffolder-focus.md`.
- Security and licensing: `SECURITY.md`, `LICENSE`, `NOTICE`.

**Consult [PROJECT_DEEP_DIVE.md](PROJECT_DEEP_DIVE.md) for the technical details; this short file deliberately avoids duplicating the full reference.**
