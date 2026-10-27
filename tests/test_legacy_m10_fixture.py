"""Actual pre-M11 template fixture tests, preserving original M10 source contract."""
from pathlib import Path
import shutil

from aet_scaffolder.validator import validate_project

FIXTURE = Path(__file__).parent / "fixtures" / "pre_m11_tool_agent"


def test_doctor_accepts_real_m10_project_without_manifest():
    assert not (FIXTURE / ".aet-template.json").exists()
    for new_file in ("Dockerfile", ".dockerignore", ".github/workflows/ci.yml",
                     "app/foundation.py", "tests/test_foundation.py"):
        assert not (FIXTURE / new_file).exists(), new_file
    report = validate_project(FIXTURE)
    assert report.ok, report.as_dict()
    assert report.checks[0].name == "template_identity"
    assert "Legacy" in report.checks[0].message


def test_legacy_profile_still_rejects_missing_original_required_file(tmp_path):
    target = tmp_path / "old-project"
    shutil.copytree(FIXTURE, target)
    (target / "app" / "workflow.py").unlink()
    report = validate_project(target)
    assert not report.ok
    assert any(c.name == "file:app/workflow.py" and not c.passed for c in report.checks)


def test_old_project_fixture_has_no_unexpanded_placeholders():
    for path in FIXTURE.rglob("*"):
        if path.is_file():
            assert "__PROJECT_NAME__" not in path.read_text(encoding="utf-8")
