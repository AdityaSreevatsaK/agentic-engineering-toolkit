"""M17: Strands provider options and offline package contents."""
import pytest
from aet_scaffolder.generator import generate, GenerationError
from aet_scaffolder.registry import get_template
from aet_scaffolder.validator import validate_project


@pytest.mark.parametrize("provider", ["mock", "bedrock", "openai", "azure-openai", "anthropic"])
def test_new_strands_providers_generate_complete_projects_offline(tmp_path, provider):
    project = generate("strands-test", output_dir=tmp_path, template="strands-agent",
                       provider=provider)
    report = validate_project(project)
    assert report.ok, report.as_dict()
    assert (project / "app/cloud_models.py").is_file()
    env = (project / ".env.example").read_text(encoding="utf-8")
    assert f"AET_PROVIDER={provider}" in env
    assert "OPENAI_API_KEY=" not in env
    assert "ANTHROPIC_API_KEY=" not in env
    assert "AZURE_OPENAI_API_KEY=" not in env
    pyproject = (project / "pyproject.toml").read_text()
    assert "strands-agents[openai]" in pyproject
    assert "strands-agents[anthropic]" in pyproject


def test_strands_does_not_expose_unimplemented_ollama_mode(tmp_path):
    assert "ollama" not in get_template("strands-agent").providers
    with pytest.raises(GenerationError, match="provider"):
        generate("bad-example", template="strands-agent", provider="ollama",
                 output_dir=tmp_path)


@pytest.mark.parametrize("provider", ["openai", "azure-openai", "anthropic"])
def test_strands_cloud_settings_do_not_accept_legacy_ollama_model_option(
        tmp_path, provider):
    with pytest.raises(GenerationError, match="--model"):
        generate("bad-example", template="strands-agent", provider=provider,
                 model="some-model", output_dir=tmp_path)
