"""M13: generated Strands SDK agent scaffolding, backward-compatible options."""
import json

import pytest

from aet_scaffolder.cli import main
from aet_scaffolder.generator import GenerationError, generate
from aet_scaffolder.validator import validate_project


@pytest.mark.parametrize("provider", ["mock", "bedrock"])
def test_strands_project_generation_and_doctor(tmp_path, provider):
    root = generate("strands-test", template="strands-agent",
                    provider=provider, output_dir=tmp_path)
    assert (root / "app" / "agent.py").is_file()
    assert (root / "app" / "offline_model.py").is_file()
    assert (root / "tests" / "test_agent.py").is_file()
    assert json.loads((root / ".aet-template.json").read_text())["template"] == "strands-agent"
    assert f"AET_PROVIDER={provider}" in (root / ".env.example").read_text()
    assert "strands-agents" in (root / "pyproject.toml").read_text()
    report = validate_project(root)
    assert report.ok, report.as_dict()


@pytest.mark.parametrize("template,provider", [
    ("strands-agent", "ollama"),
])
def test_provider_restrictions_by_template(tmp_path, template, provider):
    with pytest.raises(GenerationError, match="provider"):
        generate("blocked", template=template, provider=provider, output_dir=tmp_path)


def test_bedrock_does_not_accept_ollama_only_model_option(tmp_path):
    with pytest.raises(GenerationError, match="--model"):
        generate("blocked", template="strands-agent", provider="bedrock",
                 model="some-model", output_dir=tmp_path)


def test_previous_defaults_remain_unchanged(tmp_path):
    root = generate("legacy", output_dir=tmp_path)
    assert (root / "app" / "workflow.py").exists()
    assert "AET_PROVIDER=mock" in (root / ".env.example").read_text()


def test_cli_lists_strands_and_generates_bedrock(tmp_path, capsys):
    assert main(["list"]) == 0
    assert "strands-agent" in capsys.readouterr().out
    assert main(["new", "aws-demo", "--template", "strands-agent",
                 "--provider", "bedrock", "--output-dir", str(tmp_path)]) == 0
    assert (tmp_path / "aws-demo" / "app" / "tools.py").exists()
