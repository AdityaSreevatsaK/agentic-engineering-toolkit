"""Opt-in hashed dependency lock and digest-pinned production Dockerfile.

Run on the deployment target's Python 3.12 platform with pip-tools installed.
Default local generated Dockerfiles and editable-install workflows are unchanged.
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_EXTRA = re.compile(r"[a-z][a-z0-9-]*\Z")


def production_dockerfile(digest: str) -> str:
    if not _DIGEST.fullmatch(digest):
        raise ValueError("Python image digest must be sha256 followed by 64 lowercase hex digits")
    image = f"python:3.12-slim@{digest}"
    return f"""# Opt-in production reference; review ingress, TLS, identity and provider budgets.
# Base image digest and dependency hashes must be refreshed deliberately.
FROM {image} AS builder
ENV PIP_NO_CACHE_DIR=1
WORKDIR /srv/app
COPY . .
RUN python -m pip install --require-hashes -r requirements.lock && \\
    python -m pip wheel --no-deps --no-build-isolation --wheel-dir /wheels .

FROM {image}
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PIP_NO_CACHE_DIR=1 \\
    AET_PROVIDER=mock \\
    AET_SECURITY_MODE=hardened
WORKDIR /srv/app
COPY . .
COPY --from=builder /wheels /wheels
RUN python -m pip install --require-hashes -r requirements.lock && \\
    python -m pip install --no-deps /wheels/*.whl && \\
    useradd --uid 10001 --create-home appuser && \\
    chown -R appuser:appuser /srv/app
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=4s --start-period=20s --retries=3 \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""


def prepare_deployment(
    project: Path, digest: str, extras: tuple[str, ...] = (), *,
    overwrite: bool = False,
) -> tuple[Path, Path]:
    """Compile hashed pins and write production Dockerfile only after success."""
    dockerfile = production_dockerfile(digest)
    project = project.resolve()
    if not (project / ".aet-template.json").is_file():
        raise ValueError("Expected a generated AET project")
    if not (project / "pyproject.toml").is_file():
        raise ValueError("Generated project is missing pyproject.toml")
    if any(not _EXTRA.fullmatch(extra) for extra in extras):
        raise ValueError("Invalid optional dependency extra")
    lock_target = project / "requirements.lock"
    docker_target = project / "Dockerfile.production"
    if any(path.is_symlink() for path in (lock_target, docker_target)):
        raise ValueError("Refusing to replace a symlink")
    if not overwrite and (lock_target.exists() or docker_target.exists()):
        raise ValueError("Deployment files already exist; use --overwrite to regenerate")

    with tempfile.TemporaryDirectory(prefix=".aet-deploy-", dir=project) as temporary:
        lock = Path(temporary) / "requirements.lock"
        command = [
            sys.executable, "-m", "piptools", "compile",
            "--generate-hashes", "--all-build-deps", "--strip-extras",
            "--output-file", str(lock),
        ]
        for extra in extras:
            command.extend(["--extra", extra])
        command.append(str(project / "pyproject.toml"))
        subprocess.run(command, check=True, cwd=project)
        if not lock.is_file() or "--hash=sha256:" not in lock.read_text(encoding="utf-8"):
            raise ValueError("Dependency resolver did not produce a hashed lock file")
        generated_dockerfile = Path(temporary) / "Dockerfile.production"
        generated_dockerfile.write_text(dockerfile, encoding="utf-8")
        os.replace(lock, lock_target)
        os.replace(generated_dockerfile, docker_target)
    return lock_target, docker_target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--python-image-digest", required=True)
    parser.add_argument("--extra", action="append", default=[])
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        lock, dockerfile = prepare_deployment(
            args.project, args.python_image_digest, tuple(args.extra),
            overwrite=args.overwrite,
        )
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"Deployment preparation failed: {type(exc).__name__}\n")
    print(f"Prepared {lock.name} and {dockerfile.name}. Review before deploying.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
