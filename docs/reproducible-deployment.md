# Reproducible generated deployment (opt-in)

The default Dockerfiles and dependency ranges remain simple for local development. For deployment, generate a **hashed dependency lock** and **digest-pinned production Dockerfile** from a fresh generated project:

1. Use Python 3.12 on the target deployment platform. Install a reviewed/pinned version of `pip-tools`.
2. Obtain and independently verify the **manifest digest** for the approved `python:3.12-slim` base image, including the target architecture.
3. Run `python scripts/prepare_deployment.py ./my-generated-project --python-image-digest sha256:<64-hex-digits>` from the AET repository. Pass `--extra openai`, `--extra bedrock`, etc., for the selected provider. The script invokes `pip-compile --generate-hashes --all-build-deps`.
4. Review `requirements.lock` and `Dockerfile.production`. Commit the lock alongside the **generated deployment project**, not as a universal cross-platform lock for all users. Build using `docker build -f Dockerfile.production .` from that project.
5. Scan the image and SBOM, run the generated tests, and validate the deployment's authentication, tenant corpora, TLS, provider access, billing quotas and readiness before promotion.

The script refuses to overwrite existing deployment files without `--overwrite`. It does not download a model, contact a cloud inference API, verify the supplied image digest, or certify a build. Locks are platform/Python-version specific. Use automated image-digest and dependency update reviews; recompile and retest for every approved change.

For API security, see [hardened profile](security/hardened-profile.md). The development Dockerfile still binds to loopback in the documented host command and is **not** production-certified.
