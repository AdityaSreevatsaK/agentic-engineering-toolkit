"""Read-only verification tests with no generated app dependencies."""
import json

import pytest

from aet_scaffolder.cli import main
from aet_scaffolder.generator import generate
from aet_scaffolder.validator import validate_project


@pytest.mark.parametrize("provider", ["mock", "ollama"])
def test_doctor_validates_both_generated_variants(tmp_path, provider):
    project = generate(f"{provider}-app", output_dir=tmp_path, provider=provider)
    report = validate_project(project)
    assert report.ok, report.as_dict()
    assert all(item.passed for item in report.checks)


def test_doctor_missing_project(tmp_path):
    report = validate_project(tmp_path / "missing")
    assert not report.ok
    assert report.checks[0].name == "project_directory"


def test_doctor_detects_missing_file_without_modifying_project(tmp_path):
    project = generate("sample", output_dir=tmp_path)
    (project / "app" / "providers.py").unlink()
    report = validate_project(project)
    assert not report.ok
    assert any(c.name == "file:app/providers.py" and not c.passed for c in report.checks)
    assert not (project / "app" / "providers.py").exists()


def test_doctor_detects_syntax_error(tmp_path):
    project = generate("sample", output_dir=tmp_path)
    (project / "app" / "workflow.py").write_text("def broken(:\n", encoding="utf-8")
    report = validate_project(project)
    assert not report.ok
    assert any(c.name == "python_syntax" and not c.passed for c in report.checks)


def test_doctor_detects_bad_metadata(tmp_path):
    project = generate("sample", output_dir=tmp_path)
    (project / "pyproject.toml").write_text("[project]\nname = 999\n", encoding="utf-8")
    report = validate_project(project)
    assert not report.ok
    assert any(c.name == "project_metadata" and not c.passed for c in report.checks)


def test_doctor_detects_missing_config(tmp_path):
    project = generate("sample", output_dir=tmp_path)
    (project / ".env.example").write_text("AET_PROVIDER=mock\n", encoding="utf-8")
    report = validate_project(project)
    assert not report.ok
    assert any(c.name == "sample_configuration" and not c.passed for c in report.checks)


def test_doctor_cli_json_output(tmp_path, capsys):
    project = generate("sample", output_dir=tmp_path)
    assert main(["doctor", str(project), "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is True
    assert len(result["checks"]) >= 10


def test_doctor_cli_exit_code_for_bad_project(tmp_path, capsys):
    assert main(["doctor", str(tmp_path / "missing")]) == 1
    assert "FAIL" in capsys.readouterr().out


def test_list_output(capsys):
    assert main(["list"]) == 0
    output = capsys.readouterr().out
    assert "tool-agent" in output
    assert "mock" in output
    assert "ollama" in output


def test_version_output(capsys):
    with pytest.raises(SystemExit) as error:
        main(["--version"])
    assert error.value.code == 0
    assert "0.3.0" in capsys.readouterr().out
