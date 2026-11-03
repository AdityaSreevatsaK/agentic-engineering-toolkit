"""Keep independent generated LangChain cloud adapters behaviorally aligned."""
from pathlib import Path


TEMPLATES = Path(__file__).resolve().parents[1] / "src" / "aet_scaffolder" / "templates"


def test_langchain_provider_implementations_remain_identical():
    tool = (TEMPLATES / "tool_agent" / "app" / "cloud_providers.py").read_text(encoding="utf-8")
    rag = (TEMPLATES / "langgraph_rag" / "app" / "cloud_providers.py").read_text(encoding="utf-8")
    assert tool == rag, "Update both standalone templates when changing cloud adapter policy"
    assert '"timeout": timeout' in tool
    assert '"max_retries": retries' in tool
