"""M18: native LlamaIndex scaffold contracts remain safe and self-contained."""
import json
import pytest

from aet_scaffolder.cli import main
from aet_scaffolder.generator import GenerationError, generate
from aet_scaffolder.registry import SUPPORTED_TEMPLATES, get_template
from aet_scaffolder.validator import validate_project


@pytest.mark.parametrize("provider", ["mock", "ollama", "openai", "azure-openai", "anthropic", "bedrock"])
def test_llamaindex_project_generation_and_doctor(tmp_path, provider):
    project = generate("index-demo", template="llamaindex-rag",
                       provider=provider, output_dir=tmp_path)
    assert (project / "app" / "retrieval.py").exists()
    assert (project / "app" / "providers.py").exists()
    assert (project / "data" / "knowledge.jsonl").exists()
    assert (project / "tests" / "test_retrieval.py").exists()
    assert json.loads((project / ".aet-template.json").read_text()) == {
        "schema_version": 1, "template": "llamaindex-rag",
    }
    assert f"AET_PROVIDER={provider}" in (project / ".env.example").read_text()
    assert "OPENAI_API_KEY=" not in (project / ".env.example").read_text()
    report = validate_project(project)
    assert report.ok, report.as_dict()


def test_llamaindex_framework_is_real_without_langgraph(tmp_path):
    assert "llamaindex-rag" in SUPPORTED_TEMPLATES
    spec = get_template("llamaindex-rag")
    assert "llama-index-core" in spec.required_dependencies
    assert "langgraph" not in spec.required_dependencies
    project = generate("index-demo", template="llamaindex-rag", output_dir=tmp_path)
    assert "SimpleKeywordTableIndex" in (project / "app" / "retrieval.py").read_text()
    metadata = (project / "pyproject.toml").read_text()
    assert "llama-index-core" in metadata and "langgraph" not in metadata


def test_existing_default_template_unchanged(tmp_path):
    project = generate("legacy-default", output_dir=tmp_path)
    assert json.loads((project / ".aet-template.json").read_text())["template"] == "tool-agent"


def test_llamaindex_rejects_nonollama_model_flag(tmp_path):
    with pytest.raises(GenerationError, match="--model"):
        generate("invalid-demo", template="llamaindex-rag", provider="openai",
                 model="gpt-test", output_dir=tmp_path)


def test_cli_lists_and_generates_new_template(tmp_path, capsys):
    assert main(["list"]) == 0
    assert "Template: llamaindex-rag" in capsys.readouterr().out
    assert main(["new", "new-index", "--template", "llamaindex-rag",
                 "--output-dir", str(tmp_path)]) == 0
    assert (tmp_path / "new-index" / "app" / "retrieval.py").exists()


def test_private_corpora_are_gitignored(tmp_path):
    project = generate("index-demo", template="llamaindex-rag", output_dir=tmp_path)
    ignore = (project / ".gitignore").read_text()
    assert "data/*" in ignore and "!data/knowledge.jsonl" in ignore


def test_llamaindex_generation_never_overwrites(tmp_path):
    generate("index-demo", template="llamaindex-rag", output_dir=tmp_path)
    with pytest.raises(GenerationError, match="overwrite"):
        generate("index-demo", template="llamaindex-rag", output_dir=tmp_path)
