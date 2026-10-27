"""M16: all cloud selections scaffold valid, offline LangGraph applications."""
import pytest

from aet_scaffolder.generator import GenerationError, generate
from aet_scaffolder.registry import get_template
from aet_scaffolder.validator import validate_project


@pytest.mark.parametrize("template", ["tool-agent", "langgraph-rag"])
@pytest.mark.parametrize("provider", ["openai", "azure-openai", "anthropic", "bedrock"])
def test_generated_cloud_provider_projects_pass_doctor_without_credentials(
        tmp_path, template, provider):
    project = generate("cloud-demo", template=template, provider=provider,
                       output_dir=tmp_path)
    assert validate_project(project).ok
    env = (project / ".env.example").read_text(encoding="utf-8")
    assert f"AET_PROVIDER={provider}" in env
    assert "OPENAI_API_KEY=" not in env
    assert "ANTHROPIC_API_KEY=" not in env
    assert (project / "app" / "cloud_providers.py").is_file()
    meta = (project / "pyproject.toml").read_text()
    for extra in ('openai =', 'azure-openai =', 'anthropic =', 'bedrock ='):
        assert extra in meta
    source = (project / "app" / "cloud_providers.py").read_text()
    assert "from langchain_openai import ChatOpenAI" in source
    assert "from langchain_openai import AzureChatOpenAI" in source
    assert "from langchain_anthropic import ChatAnthropic" in source
    assert "from langchain_aws import ChatBedrock" in source


@pytest.mark.parametrize("template", ["tool-agent", "langgraph-rag"])
def test_existing_default_and_local_ollama_options_remain_supported(tmp_path, template):
    assert {"mock", "ollama"} <= set(get_template(template).providers)
    for provider in ("mock", "ollama"):
        output = tmp_path / provider
        output.mkdir()
        project = generate("sample-agent", template=template, provider=provider,
                           output_dir=output)
        assert validate_project(project).ok


@pytest.mark.parametrize("template", ["tool-agent", "langgraph-rag", "strands-agent"])
def test_cli_ollama_model_argument_is_not_repurposed_for_cloud(tmp_path, template):
    with pytest.raises(GenerationError, match="--model"):
        generate("bad-example", template=template, provider="bedrock",
                 model="some-model", output_dir=tmp_path)


def test_strands_does_not_claim_unsupported_chat_providers(tmp_path):
    with pytest.raises(GenerationError, match="provider"):
        generate("bad-example", template="strands-agent", provider="openai",
                 output_dir=tmp_path)
