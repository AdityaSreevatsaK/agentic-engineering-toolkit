"""Licence metadata and shipped notices for AET and generated projects."""
import tomllib
from pathlib import Path

import pytest

from aet_scaffolder.generator import generate
from aet_scaffolder.validator import validate_project

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_PATHS = [
    ROOT,
    ROOT / "packages" / "agent-quality-kit",
    ROOT / "packages" / "agent-provider-contract",
]


@pytest.mark.parametrize("path", PACKAGE_PATHS)
def test_each_installable_distribution_has_apache_licence(path):
    licence = (path / "LICENSE").read_text(encoding="utf-8")
    notice = (path / "NOTICE").read_text(encoding="utf-8")
    metadata = tomllib.loads((path / "pyproject.toml").read_text(encoding="utf-8"))
    assert "Apache License" in licence
    assert "Version 2.0, January 2004" in licence
    assert "TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION" in licence
    assert "Copyright 2026 AdityaSreevatsaK" in notice
    assert metadata["project"]["license"]["text"] == "Apache-2.0"


@pytest.mark.parametrize("template", ["tool-agent", "langgraph-rag", "strands-agent"])
def test_new_generated_projects_include_licence_and_notice(tmp_path, template):
    app = generate("licensed-example", output_dir=tmp_path, template=template)
    assert (app / "LICENSE").read_text(encoding="utf-8") == (
        ROOT / "LICENSE"
    ).read_text(encoding="utf-8")
    assert (app / "NOTICE").read_text(encoding="utf-8") == (
        ROOT / "NOTICE"
    ).read_text(encoding="utf-8")
    metadata = tomllib.loads((app / "pyproject.toml").read_text(encoding="utf-8"))
    assert metadata["project"]["license"]["text"] == "Apache-2.0"
    assert validate_project(app).ok
