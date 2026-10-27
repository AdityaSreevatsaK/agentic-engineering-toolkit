"""Keep M15's documented path and server lifecycle friction addressed."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADOPTION = ROOT / "docs" / "adoption"


def test_trial_includes_absolute_path_and_restart_procedure():
    doc = (ADOPTION / "independent-trial.md").read_text(encoding="utf-8")
    assert "Path('data/knowledge.jsonl').resolve()" in doc
    assert "pilot-rag" in doc
    assert "Ctrl+C" in doc
    assert "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000" in doc
    assert "does not require a server restart" in doc


def test_evidence_separates_author_testing_from_independent_adoption():
    evidence = (ADOPTION / "evidence-register.md").read_text(encoding="utf-8")
    assert "Author-operated RAG smoke test" in evidence
    assert "29 passed, 1 skipped" in evidence
    assert "Independent fresh-user execution" in evidence
    assert "Not collected" in evidence
