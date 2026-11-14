"""Contract tests for bounded, isolated generated-application installations.

Fake only subprocess/venv execution. Real scaffolder generation still occurs;
no cloud access, dependency downloads or Docker are required by these tests.
"""
from collections import Counter
from pathlib import Path
from threading import Barrier, Lock

import pytest

from aet_scaffolder.registry import SUPPORTED_TEMPLATES
from scripts import isolated_install_smoke


class _FakeEnvBuilder:
    def __init__(self, *, with_pip: bool):
        assert with_pip

    def create(self, path):
        Path(path).mkdir(parents=True)


def test_parallel_jobs_keep_apps_isolated_and_preserve_all_results(tmp_path, monkeypatch):
    """A barrier proves two installations may overlap without import/path bleed."""
    barrier = Barrier(2, timeout=10)
    lock = Lock()
    calls = []

    def fake_run(args, *, cwd, stage, timeout=420, env=None):
        with lock:
            calls.append((str(args[0]), Path(cwd), stage, env))
        if stage.endswith("/install"):
            barrier.wait()
        if stage.endswith("/pytest"):
            return "12 passed in 0.10s\n"
        if stage.endswith("/versions"):
            return "synthetic-package==1\n"
        return ""

    monkeypatch.setattr(isolated_install_smoke.venv, "EnvBuilder", _FakeEnvBuilder)
    monkeypatch.setattr(isolated_install_smoke, "_run", fake_run)

    report_dir = tmp_path / "versions"
    results = isolated_install_smoke.verify_isolated_installations(report_dir, jobs=2)
    assert [result["template"] for result in results] == list(SUPPORTED_TEMPLATES)
    assert all(result["venv_isolated"] and result["actual_asgi_probe"] for result in results)
    assert all(result["generated_app_tests_passed"] == 12 for result in results)

    expected = Counter({
        f"{template}/{stage}": 1
        for template in SUPPORTED_TEMPLATES
        for stage in ("install", "pip-check", "pytest", "api", "versions")
    })
    assert Counter(call[2] for call in calls) == expected

    install_interpreters = {call[0] for call in calls if call[2].endswith("/install")}
    assert len(install_interpreters) == len(SUPPORTED_TEMPLATES)
    for interpreter, cwd, stage, env in calls:
        template = stage.split("/")[0]
        assert cwd.name == f"isolated-{template}"
        assert f"venv-{template}" in Path(interpreter).parts
        if stage.endswith("/pytest") or stage.endswith("/api"):
            assert env is not None and env["AET_PROVIDER"] == "mock"

    for template in SUPPORTED_TEMPLATES:
        assert (report_dir / f"{template}.txt").read_text() == "synthetic-package==1\n"


@pytest.mark.parametrize("jobs", [0, -1, 5])
def test_invalid_parallelism_fails_without_creating_files(tmp_path, jobs):
    report_dir = tmp_path / "versions"
    with pytest.raises(ValueError, match="jobs must be between"):
        isolated_install_smoke.verify_isolated_installations(report_dir, jobs=jobs)
    assert not report_dir.exists()


def test_refuse_existing_evidence_directory(tmp_path):
    report_dir = tmp_path / "existing"
    report_dir.mkdir()
    with pytest.raises(ValueError, match="overwrite"):
        isolated_install_smoke.verify_isolated_installations(report_dir, jobs=2)
