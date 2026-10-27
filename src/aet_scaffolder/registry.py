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
    description="Deterministic LangGraph tool routing with mock or local Ollama responses",
    providers=("mock", "ollama"),
    required_files=(
        "README.md", ".gitignore", ".env.example", "pyproject.toml",
        ".dockerignore", "Dockerfile", ".github/workflows/ci.yml",
        "app/foundation.py", "tests/test_foundation.py",
        "app/__init__.py", "app/config.py", "app/main.py",
        "app/providers.py", "app/tools.py", "app/workflow.py",
        "tests/test_app.py", "tests/test_providers.py", "tests/test_tools.py",
    ),
    required_dependencies=frozenset(
        {"fastapi", "langgraph", "uvicorn", "pydantic-settings"}
    ),
    required_env_fields=(
        "AET_PROVIDER=", "AET_OLLAMA_MODEL=", "AET_OLLAMA_BASE_URL=",
        "AET_LOG_LEVEL=",
    ),
)

_LANGGRAPH_RAG = TemplateSpec(
    name="langgraph-rag",
    directory="langgraph_rag",
    description="Local BM25 retrieval-augmented LangGraph answer workflow",
    providers=("mock", "ollama"),
    required_files=(
        "README.md", ".gitignore", ".env.example", "pyproject.toml",
        ".dockerignore", "Dockerfile", ".github/workflows/ci.yml",
        "app/foundation.py", "tests/test_foundation.py",
        "data/knowledge.jsonl",
        "app/__init__.py", "app/config.py", "app/knowledge.py",
        "app/retrieval.py", "app/providers.py", "app/workflow.py",
        "app/main.py", "app/ingest.py",
        "tests/test_app.py", "tests/test_retrieval.py", "tests/test_ingest.py",
    ),
    required_dependencies=frozenset(
        {"fastapi", "langgraph", "uvicorn", "pydantic-settings"}
    ),
    required_env_fields=(
        "AET_PROVIDER=", "AET_OLLAMA_MODEL=", "AET_OLLAMA_BASE_URL=",
        "AET_KNOWLEDGE_PATH=", "AET_LOG_LEVEL=",
    ),
)

_STRANDS_AGENT = TemplateSpec(
    name="strands-agent",
    directory="strands_agent",
    description="Strands agent with offline SDK model and opt-in cloud providers",
    providers=("mock", "bedrock", "openai", "azure-openai", "anthropic"),
    required_files=(
        "README.md", ".gitignore", ".env.example", "pyproject.toml",
        ".dockerignore", "Dockerfile", ".github/workflows/ci.yml",
        "app/foundation.py", "tests/test_foundation.py",
        "app/__init__.py", "app/config.py", "app/agent.py", "app/tools.py",
        "app/offline_model.py", "app/main.py",
        "tests/test_api.py", "tests/test_agent.py",
    ),
    required_dependencies=frozenset(
        {"fastapi", "uvicorn", "strands-agents", "pydantic-settings"}
    ),
    required_env_fields=("AET_PROVIDER=", "AET_AWS_REGION=", "AET_BEDROCK_MODEL_ID=", "AET_LOG_LEVEL="),
)

TEMPLATES: Mapping[str, TemplateSpec] = MappingProxyType(
    {spec.name: spec for spec in (_TOOL_AGENT, _LANGGRAPH_RAG, _STRANDS_AGENT)}
)
SUPPORTED_TEMPLATES = tuple(TEMPLATES)


def get_template(name: str) -> TemplateSpec:
    """Return a known template, rejecting unknown names explicitly."""
    try:
        return TEMPLATES[name]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"unsupported template: {name!r}") from exc
