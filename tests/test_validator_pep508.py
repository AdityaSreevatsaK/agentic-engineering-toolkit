"""PEP 508 parsing handles extras, markers and package-name normalisation."""
import pytest

from aet_scaffolder.generator import generate
from aet_scaffolder.validator import validate_project


@pytest.mark.parametrize("replacement", [
    "FastAPI[standard]>=0.110,<1",
    "FASTAPI>=0.110",
    "FastAPI @ https://example.org/packages/fastapi.whl",
])
def test_dependency_parser_accepts_valid_pep508_forms(tmp_path, replacement):
    root = generate("pep508-valid", output_dir=tmp_path)
    metadata = root / "pyproject.toml"
    metadata.write_text(metadata.read_text(encoding="utf-8").replace(
        "fastapi>=0.110,<1", replacement, 1
    ), encoding="utf-8")
    assert validate_project(root).ok


@pytest.mark.parametrize("replacement", [
    'fastapi>=0.110 ; python_version < "2.0"',
    "fastapi => 1.0",
    12,
])
def test_dependency_parser_rejects_invalid_or_inactive_requirement(
        tmp_path, replacement):
    root = generate("pep508-invalid", output_dir=tmp_path)
    metadata = root / "pyproject.toml"
    original = metadata.read_text(encoding="utf-8")
    if isinstance(replacement, str):
        mutated = original.replace("fastapi>=0.110,<1", replacement, 1)
    else:
        mutated = original.replace('"fastapi>=0.110,<1"', str(replacement), 1)
    metadata.write_text(mutated, encoding="utf-8")
    report = validate_project(root)
    assert not report.ok
    assert any(
        check.name == "project_metadata" and not check.passed
        for check in report.checks
    )
