"""Production lock preparation uses an offline fake resolver in root CI."""
from pathlib import Path

import pytest

from aet_scaffolder.generator import generate
from scripts import prepare_deployment as deploy

DIGEST = "sha256:" + "a" * 64


def test_prepare_generates_hashed_lock_and_digest_pinned_docker(tmp_path, monkeypatch):
    project = generate("deploy-demo", output_dir=tmp_path)
    calls = []

    def fake_run(command, *, check, cwd):
        calls.append(command)
        assert check and cwd == project
        assert "--generate-hashes" in command
        assert "--all-build-deps" in command
        assert "--extra" in command
        lock = Path(command[command.index("--output-file") + 1])
        lock.write_text("fastapi==0.115.0 \\\n    --hash=sha256:" + "b" * 64 + "\n")

    monkeypatch.setattr(deploy.subprocess, "run", fake_run)
    original = (project / "Dockerfile").read_text()
    lock, dockerfile = deploy.prepare_deployment(project, DIGEST, ("openai",))
    assert len(calls) == 1
    assert lock.is_file() and "--hash=sha256:" in lock.read_text()
    assert dockerfile.read_text().count("python:3.12-slim@" + DIGEST) == 2
    assert "--require-hashes" in dockerfile.read_text()
    assert "AET_SECURITY_MODE=hardened" in dockerfile.read_text()
    assert "--no-build-isolation" in dockerfile.read_text()
    assert (project / "Dockerfile").read_text() == original
    with pytest.raises(ValueError, match="already exist"):
        deploy.prepare_deployment(project, DIGEST)


@pytest.mark.parametrize("digest", ["latest", "sha256:bad", "sha256:" + "Z" * 64])
def test_invalid_image_digest_rejected(digest):
    with pytest.raises(ValueError, match="digest"):
        deploy.production_dockerfile(digest)


def test_resolver_failure_keeps_project_unchanged(tmp_path, monkeypatch):
    project = generate("deploy-demo", output_dir=tmp_path)

    def fail(*args, **kwargs):
        raise RuntimeError("Resolver unavailable")

    monkeypatch.setattr(deploy.subprocess, "run", fail)
    with pytest.raises(RuntimeError):
        deploy.prepare_deployment(project, DIGEST)
    assert not (project / "requirements.lock").exists()
    assert not (project / "Dockerfile.production").exists()
