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
        "app/__init__.py", "app/config.py", "app/main.py",
        "app/providers.py", "app/tools.py", "app/workflow.py",
        "tests/test_app.py", "tests/test_providers.py", "tests/test_tools.py",
    ),
    required_dependencies=frozenset(
        {"fastapi", "langgraph", "uvicorn", "pydantic-settings"}
    ),
    required_env_fields=(
        "AET_PROVIDER=", "AET_OLLAMA_MODEL=", "AET_OLLAMA_BASE_URL=",
    ),
)

_LANGGRAPH_RAG = TemplateSpec(
    name="langgraph-rag",
    directory="langgraph_rag",
    description="Local BM25 retrieval-augmented LangGraph answer workflow",
    providers=("mock", "ollama"),
    required_files=(
        "README.md", ".gitignore", ".env.example", "pyproject.toml",
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
        "AET_KNOWLEDGE_PATH=",
    ),
)

TEMPLATES: Mapping[str, TemplateSpec] = MappingProxyType(
    {spec.name: spec for spec in (_TOOL_AGENT, _LANGGRAPH_RAG)}
)
SUPPORTED_TEMPLATES = tuple(TEMPLATES)


def get_template(name: str) -> TemplateSpec:
    """Return a known template, rejecting unknown names explicitly."""
    try:
        return TEMPLATES[name]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"unsupported template: {name!r}") from exc
