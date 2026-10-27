"""Template registry and backwards-compatibility contract tests."""
import json

import pytest

from aet_scaffolder.cli import main
from aet_scaffolder.generator import GenerationError, generate
from aet_scaffolder.registry import MANIFEST_FILE, SUPPORTED_TEMPLATES, get_template
from aet_scaffolder.validator import validate_project


def test_registered_tool_agent_metadata():
    spec = get_template("tool-agent")
    assert SUPPORTED_TEMPLATES == ("tool-agent", "langgraph-rag", "strands-agent")
    assert spec.directory == "tool_agent"
    assert {"mock", "ollama", "openai", "azure-openai", "anthropic", "bedrock"} == set(spec.providers)
    assert "app/workflow.py" in spec.required_files


def test_reject_unregistered_template(tmp_path):
    with pytest.raises(GenerationError, match="unsupported template"):
        generate("example", output_dir=tmp_path, template="unregistered")


@pytest.mark.parametrize("provider", ["mock", "ollama"])
def test_generated_manifest_and_profile(tmp_path, provider):
    project = generate("example", output_dir=tmp_path, template="tool-agent", provider=provider)
    assert json.loads((project / MANIFEST_FILE).read_text(encoding="utf-8")) == {
        "schema_version": 1, "template": "tool-agent",
    }
    report = validate_project(project)
    assert report.ok, report.as_dict()
    assert any(c.name == "template_identity" and "Registered template" in c.message for c in report.checks)


def test_doctor_supports_existing_pre_m11_project(tmp_path):
    project = generate("example", output_dir=tmp_path)
    (project / MANIFEST_FILE).unlink()
    report = validate_project(project)
    assert report.ok, report.as_dict()
    assert any(c.name == "template_identity" and "Legacy" in c.message for c in report.checks)


@pytest.mark.parametrize(
    "data",
    [
        "{", "[]",
        '{"schema_version":2,"template":"tool-agent"}',
        '{"schema_version":1,"template":"not-registered"}',
        '{"schema_version":true,"template":"tool-agent"}',
    ],
)
def test_doctor_rejects_invalid_manifest_without_mutation(tmp_path, data):
    project = generate("example", output_dir=tmp_path)
    marker = project / MANIFEST_FILE
    marker.write_text(data, encoding="utf-8")
    report = validate_project(project)
    assert not report.ok
    assert report.checks[0].name == "template_identity"
    assert marker.read_text(encoding="utf-8") == data


def test_cli_explicit_template_and_list_backward_compatible(tmp_path, capsys):
    assert main(["list"]) == 0
    output = capsys.readouterr().out
    assert "Template: tool-agent" in output
    assert "Template: langgraph-rag" in output
    assert "Template: strands-agent" in output
    assert "Providers: mock, ollama" in output
    assert main(["new", "example", "--template", "tool-agent", "--output-dir", str(tmp_path)]) == 0
    assert (tmp_path / "example" / MANIFEST_FILE).is_file()
