"""Declarative inventory of project templates and their validation profiles.

Add future framework templates here without changing the CLI or project doctor.
The registry contains metadata only; generated apps remain self-contained.
"""
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

DEFAULT_TEMPLATE = "tool-agent"
MANIFEST_FILE = ".aet-template.json"
MANIFEST_VERSION = 1

# Shared authoring-time contracts preserve self-contained generated projects.
_COMMON_FOUNDATION_FILES = (
    "README.md", ".gitignore", ".env.example", "pyproject.toml",
    ".dockerignore", "Dockerfile", ".github/workflows/ci.yml",
    "app/foundation.py", "tests/test_foundation.py",
)
_LANGCHAIN_PROVIDERS = ("mock", "ollama", "openai", "azure-openai", "anthropic", "bedrock")
_LANGCHAIN_DEPS = frozenset({"fastapi", "langgraph", "uvicorn", "pydantic-settings"})
# Doctor validates all documented options, not just the default/mock provider.
_LANGCHAIN_CLOUD_FIELDS = (
    "AET_OPENAI_MODEL=", "AET_AZURE_OPENAI_DEPLOYMENT=",
    "AET_AZURE_OPENAI_ENDPOINT=", "AET_AZURE_OPENAI_API_VERSION=",
    "AET_ANTHROPIC_MODEL=", "AET_BEDROCK_MODEL_ID=", "AET_AWS_REGION=",
    "AET_MODEL_TIMEOUT_SECONDS=", "AET_MODEL_MAX_RETRIES=",
)
_LANGCHAIN_BASE_FIELDS = (
    "AET_PROVIDER=", "AET_OLLAMA_MODEL=", "AET_OLLAMA_BASE_URL=",
    "AET_OLLAMA_TIMEOUT_SECONDS=", "AET_LOG_LEVEL=",
)


@dataclass(frozen=True)
class TemplateSpec:
    name: str
    directory: str
    description: str
    providers: tuple[str, ...]
    required_files: tuple[str, ...]
    required_dependencies: frozenset[str]
    required_env_fields: tuple[str, ...]


_TOOL_AGENT = TemplateSpec(
    name="tool-agent",
    directory="tool_agent",
    description="Deterministic LangGraph tool routing with optional cloud chat providers",
    providers=_LANGCHAIN_PROVIDERS,
    required_files=(
        *_COMMON_FOUNDATION_FILES,
        "app/__init__.py", "app/config.py", "app/main.py",
        "app/providers.py", "app/cloud_providers.py", "app/tools.py", "app/workflow.py",
        "tests/test_app.py", "tests/test_providers.py", "tests/test_tools.py",
    ),
    required_dependencies=_LANGCHAIN_DEPS,
    required_env_fields=(*_LANGCHAIN_BASE_FIELDS, *_LANGCHAIN_CLOUD_FIELDS),
)

_LANGGRAPH_RAG = TemplateSpec(
    name="langgraph-rag",
    directory="langgraph_rag",
    description="Local BM25 RAG with optional cloud chat generation",
    providers=_LANGCHAIN_PROVIDERS,
    required_files=(
        *_COMMON_FOUNDATION_FILES,
        "data/knowledge.jsonl",
        "app/__init__.py", "app/config.py", "app/knowledge.py",
        "app/retrieval.py", "app/providers.py", "app/cloud_providers.py", "app/workflow.py",
        "app/main.py", "app/ingest.py",
        "tests/test_app.py", "tests/test_retrieval.py", "tests/test_ingest.py",
    ),
    required_dependencies=_LANGCHAIN_DEPS,
    required_env_fields=(
        *_LANGCHAIN_BASE_FIELDS, *_LANGCHAIN_CLOUD_FIELDS,
        "AET_KNOWLEDGE_PATH=", "AET_TOP_K=",
    ),
)

_STRANDS_AGENT = TemplateSpec(
    name="strands-agent",
    directory="strands_agent",
    description="Strands agent with offline SDK model and opt-in cloud providers",
    providers=("mock", "bedrock", "openai", "azure-openai", "anthropic"),
    required_files=(
        *_COMMON_FOUNDATION_FILES,
        "app/__init__.py", "app/config.py", "app/agent.py", "app/tools.py",
        "app/offline_model.py", "app/main.py",
        "tests/test_api.py", "tests/test_agent.py",
    ),
    required_dependencies=frozenset(
        {"fastapi", "uvicorn", "strands-agents", "pydantic-settings"}
    ),
    required_env_fields=(
        "AET_PROVIDER=", "AET_AWS_REGION=", "AET_BEDROCK_MODEL_ID=",
        "AET_MODEL_TIMEOUT_SECONDS=", "AET_MODEL_MAX_RETRIES=", "AET_LOG_LEVEL=",
        "AET_OPENAI_MODEL=", "AET_ANTHROPIC_MODEL=",
        "AET_ANTHROPIC_MAX_TOKENS=", "AET_AZURE_OPENAI_DEPLOYMENT=",
        "AET_AZURE_OPENAI_ENDPOINT=", "AET_AZURE_OPENAI_API_VERSION=",
    ),
)

_LLAMAINDEX_RAG = TemplateSpec(
    name="llamaindex-rag",
    directory="llamaindex_rag",
    description="Native offline LlamaIndex keyword retrieval with optional model synthesis",
    providers=_LANGCHAIN_PROVIDERS,
    required_files=(
        "README.md", ".gitignore", ".env.example", "pyproject.toml",
        ".dockerignore", "Dockerfile", ".github/workflows/ci.yml",
        "app/__init__.py", "app/config.py", "app/foundation.py",
        "app/knowledge.py", "app/retrieval.py", "app/providers.py", "app/main.py",
        "data/knowledge.jsonl", "tests/test_foundation.py",
        "tests/test_app.py", "tests/test_retrieval.py",
        "tests/test_providers.py", "tests/test_config.py",
    ),
    required_dependencies=frozenset(
        {"fastapi", "uvicorn", "pydantic-settings", "llama-index-core"}
    ),
    required_env_fields=(
        "AET_PROVIDER=", "AET_KNOWLEDGE_PATH=", "AET_TOP_K=",
        "AET_OLLAMA_MODEL=", "AET_OLLAMA_BASE_URL=", "AET_LOG_LEVEL=",
        "AET_OPENAI_MODEL=", "AET_AZURE_OPENAI_MODEL=",
        "AET_AZURE_OPENAI_DEPLOYMENT=", "AET_AZURE_OPENAI_ENDPOINT=",
        "AET_AZURE_OPENAI_API_VERSION=", "AET_ANTHROPIC_MODEL=",
        "AET_BEDROCK_MODEL_ID=", "AET_AWS_REGION=",
        "AET_MODEL_TIMEOUT_SECONDS=",
    ),
)

TEMPLATES: Mapping[str, TemplateSpec] = MappingProxyType(
    {spec.name: spec for spec in (_TOOL_AGENT, _LANGGRAPH_RAG, _STRANDS_AGENT, _LLAMAINDEX_RAG)}
)
SUPPORTED_TEMPLATES = tuple(TEMPLATES)


def get_template(name: str) -> TemplateSpec:
    """Return a known template, rejecting unknown names explicitly."""
    try:
        return TEMPLATES[name]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"unsupported template: {name!r}") from exc
