"""M12: Generated RAG source tree, profile, manifest and package-boundaries."""
import json

import pytest

from aet_scaffolder.generator import generate
from aet_scaffolder.registry import get_template
from aet_scaffolder.validator import validate_project


@pytest.mark.parametrize("provider", ["mock", "ollama"])
def test_generate_rag_works_without_cloud_accounts(tmp_path, provider):
    root = generate("knowledge-demo", output_dir=tmp_path,
                    template="langgraph-rag", provider=provider)
    assert (root / "data" / "knowledge.jsonl").is_file()
    assert (root / "app" / "retrieval.py").is_file()
    assert (root / "tests" / "test_app.py").is_file()
    assert json.loads((root / ".aet-template.json").read_text()) == {
        "schema_version": 1, "template": "langgraph-rag"
    }
    assert f"AET_PROVIDER={provider}" in (root / ".env.example").read_text()
    result = validate_project(root)
    assert result.ok, result.as_dict()


def test_rag_metadata_has_no_aea_runtime_dependency(tmp_path):
    spec = get_template("langgraph-rag")
    assert "app/retrieval.py" in spec.required_files
    assert "langgraph" in spec.required_dependencies
    assert not any("aet_quality" in part or "agent_accelerator" in part
                   for part in spec.required_files)
    generated = generate("rag-project", output_dir=tmp_path, template="langgraph-rag")
    assert "aet-agent-quality" not in (generated / "pyproject.toml").read_text()
    assert "agent-accelerator" not in (generated / "pyproject.toml").read_text()


def test_rag_generation_does_not_overwrite_existing_path(tmp_path):
    root = generate("rag-project", output_dir=tmp_path, template="langgraph-rag")
    sentinel = root / "sentinel.txt"
    sentinel.write_text("preserve")
    from aet_scaffolder.generator import GenerationError
    with pytest.raises(GenerationError, match="overwrite"):
        generate("rag-project", output_dir=tmp_path, template="langgraph-rag")
    assert sentinel.read_text() == "preserve"


def test_private_local_corpora_are_ignored(tmp_path):
    project = generate("rag-project", output_dir=tmp_path, template="langgraph-rag")
    ignore = (project / ".gitignore").read_text(encoding="utf-8")
    assert ".env.*" in ignore
    assert "data/*" in ignore
    assert "!data/knowledge.jsonl" in ignore
