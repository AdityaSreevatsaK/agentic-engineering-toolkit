# Reproducible generated deployment (opt-in)

The default Dockerfiles and dependency ranges remain simple for local development. For deployment, generate a **hashed dependency lock** and **digest-pinned production Dockerfile** from a fresh generated project:

1. Use Python 3.12 on the target deployment platform. Install a reviewed/pinned version of `pip-tools`.
2. Obtain and independently verify the **manifest digest** for the approved `python:3.12-slim` base image, including the target architecture.
3. Run `python scripts/prepare_deployment.py ./my-generated-project --python-image-digest sha256:<64-hex-digits>` from the AET repository. Pass `--extra openai`, `--extra bedrock`, etc., for the selected provider. The script invokes `pip-compile --generate-hashes --all-build-deps`.
4. Review `requirements.lock` and `Dockerfile.production`. Commit the lock alongside the **generated deployment project**, not as a universal cross-platform lock for all users. Build using `docker build -f Dockerfile.production .` from that project.
5. Scan the image and SBOM, run the generated tests, and validate the deployment's authentication, tenant corpora, TLS, provider access, billing quotas and readiness before promotion.

The script refuses to overwrite existing deployment files without `--overwrite`. It does not download a model, contact a cloud inference API, verify the supplied image digest, or certify a build. Locks are platform/Python-version specific. Use automated image-digest and dependency update reviews; recompile and retest for every approved change.

For API security, see [hardened profile](security/hardened-profile.md). The development Dockerfile still binds to loopback in the documented host command and is **not** production-certified.

The generated production Dockerfile defaults to `AET_SECURITY_MODE=hardened`. Its tenant security implementation is already in `master` through [PR #51](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/pull/51), but deployment still requires securely injected tenant credentials (`AET_TENANT_KEYS_JSON`) and the external controls in [Issue #50](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/issues/50). **Do not deploy local mode on a public interface.**

The compiler uses `--allow-unsafe` so build tools such as setuptools are included and hash-pinned when needed by the `--no-build-isolation` wheel build. Review all generated pins before deployment.

The CI clean-build gate also checks the resulting image for fixable High/Critical OS and Python vulnerabilities using SHA-pinned Trivy. Debian 13 slim images had two fixable High zlib findings in the 15 November 2026 scan, so the generated final stage upgrades `zlib1g` from the Debian security repository. Because that repository evolves, the base digest plus Python lock alone do not make OS packages bit-for-bit reproducible. For reproducible regulated deployments, use an approved snapshot repository or build a prepatched internally pinned base image, then scan again.
