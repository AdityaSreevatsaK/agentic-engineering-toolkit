# Atomic publication and four-image Docker verification, 14 November 2026

**Scope:** AET Agent Project Scaffolder only. No AEA work, paid inference or public API deployment.

**Base:** `master` at `bed322bffae054bc257bfbfd615eb191e8898910` (post-merge PR #35). **Issue:** [#36](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/issues/36).

## Environment and directly executed evidence

- Source was inspected through the connected GitHub repository. The independent narrow fixture contains the AET generator and a minimal synthetic registry/template, **not** the complete AET source tree.
- Host used for direct execution: Linux x86_64, CPython 3.13.5, isolated standard-library-only virtual environment at `/mnt/data/aet-narrow/.venv`. Python 3.11/3.12 and Docker were not available in that execution container; DNS access to GitHub also failed.
- The patched atomic publication helper ran with real Linux `renameat2(RENAME_NOREPLACE)`. **10/10 direct standard-library tests passed**: six baseline-compatible generator tests, final-moment empty/populated-directory and dangling-symlink claims, and six concurrent generation attempts with exactly one successful publisher.
- These 10 tests establish a **narrow module behaviour**, not a full installation or compatibility certification. The new repository pytest regression tests and Docker smoke script require actual GitHub Actions validation before marking cross-platform PASS.

## Verified defect and correction

**Medium, #36, reproducible local race:** Previously, `Path.rename()` could replace a competing *empty* directory on Linux if that directory appeared between the last `exists()` check and publication. The previous post-stage recheck narrowed but did not close this window.

**Correction:** Publish a fully staged directory with the Linux `renameat2` syscall interface and `RENAME_NOREPLACE` flag. On Windows, use `Path.rename()`, whose destination-exists semantics refuse replacing existing paths. An unsupported platform, libc or filesystem fails closed rather than silently falling back to a potentially overwriting rename. Map final-moment `EEXIST` and `ENOTEMPTY` into the existing user-facing `GenerationError` no-overwrite contract.

**Preserved:** staging-directory atomic visibility on successful publication, safe project names, manifest, generated content, template/provider behaviour, Docker configurations and existing CLI contracts.

**Limits:** This protects the destination within supported filesystem semantics, not against hostile actors changing parent directory components, unreliable network filesystems, unrelated privileged processes or failures of underlying storage. Linux requires a working libc `renameat2` implementation and supporting filesystem; unsupported environments now reject generation rather than degrade silently. Windows behaviour must be verified on its own runner.

## Docker verification expansion

The existing CI workflow previously only **built** the `tool-agent` image. A new `scripts/docker_smoke.py` runs on the existing Ubuntu/Python 3.11 smoke job and:

1. Builds the generated `tool-agent`, `langgraph-rag`, `strands-agent` and `llamaindex-rag` images using their own Dockerfiles.
2. Starts each container exclusively on an automatically allocated `127.0.0.1` port.
3. Requires successful `/health`, mock `/ready`, synthetic `/invoke` or `/ask`, and invalid-question HTTP 422.
4. Removes the container after the probe; records a small, synthetic JSON summary in the existing machine-smoke artifact.
5. Never uses production credentials, cloud models, public ingress, real customer data or paid inference.

The harness itself has root-level unit tests for its loopback-only binding and request checks. The full image builds are an **Actions execution** when that job completes, not independent local Docker testing.

## Compatibility and release gates

- Required check names remain the four Windows/Linux Python 3.11/3.12 `smoke` jobs plus `quality (ruff, mypy, bandit)`.
- No extra GitHub Actions workflows were introduced; the four-image build is limited to one existing Ubuntu job to constrain duplicated effort.
- Confirm the final PR head passes every required check, verify all four Docker result entries before merging, and inspect the merged `master` run.
- A fresh independent, separately isolated Python 3.11/3.12 full-template installation and same-release `pip-audit` remain outstanding. Prior CI matrices and advisory reports must not be misrepresented as newly independent execution.
- No live cloud provider, Ollama inference, production security certification, sustained load testing or multi-team adoption is established here.

## Verification status

**At report creation:** independent narrow Linux behaviour: PASS (10/10). Full PR CI and four Docker image results: **pending execution**. Update this section with observed run IDs and outcomes before marking the work complete.
