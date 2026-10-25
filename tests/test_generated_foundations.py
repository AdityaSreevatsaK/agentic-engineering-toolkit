"""M14 scaffolder contract: production-oriented files without production claims."""
from pathlib import Path

import pytest

from aet_scaffolder.generator import generate
from aet_scaffolder.validator import validate_project


@pytest.mark.parametrize("template", ["tool-agent", "langgraph-rag", "strands-agent"])
def test_foundations_present_and_doctor_validates(tmp_path, template):
    project = generate("foundation-demo", output_dir=tmp_path, template=template)
    assert validate_project(project).ok
    for relative in (
        "Dockerfile", ".dockerignore", ".github/workflows/ci.yml",
        "app/foundation.py", "tests/test_foundation.py",
    ):
        assert (project / relative).is_file(), relative
    assert "AET_LOG_LEVEL=INFO" in (project / ".env.example").read_text()
    settings = (project / "app/config.py").read_text()
    assert 'log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]' in settings
    main = (project / "app/main.py").read_text()
    assert 'install_foundations(app)' in main
    assert '@app.get("/ready")' in main
    assert '@app.get("/health")' in main


@pytest.mark.parametrize("template", ["tool-agent", "langgraph-rag", "strands-agent"])
def test_container_and_ci_are_non_sensitive(tmp_path, template):
    root = generate("foundation-demo", output_dir=tmp_path, template=template)
    dockerfile = (root / "Dockerfile").read_text()
    ignore = (root / ".dockerignore").read_text()
    generated_ci = (root / ".github/workflows/ci.yml").read_text()
    assert "USER 10001" in dockerfile
    assert 'app.main:app' in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert ".env" in ignore and ".env.*" in ignore
    assert ".git" in ignore
    assert "AET_PROVIDER: mock" in generated_ci
    assert "python -m pytest -q" in generated_ci
    assert "contents: read" in generated_ci


def test_old_app_default_remains_tool_agent(tmp_path):
    root = generate("legacy-demo", output_dir=tmp_path)
    assert (root / "app/workflow.py").is_file()
    assert '"template": "tool-agent"' in (root / ".aet-template.json").read_text()
