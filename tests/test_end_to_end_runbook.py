"""Keep the public simple runbook, automation and registry in sync.

Cross-platform CI additionally executes a real flow in Windows PowerShell.
These assertions protect discoverability and safety; they are not a usability
study or proof of live hosted-provider access.
"""
from pathlib import Path

from aet_scaffolder.registry import TEMPLATES

ROOT = Path(__file__).resolve().parents[1]
GUIDE = (ROOT / "docs/END_TO_END_RUNBOOK.md").read_text(encoding="utf-8")
DETAIL = ROOT / "docs/END_TO_END_RUNBOOK_DETAILED.md"
RUNNER = (ROOT / "scripts/demo_windows.ps1").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_readme_is_brief_and_links_to_single_beginner_guide():
    assert len(README.splitlines()) <= 65
    assert "docs/END_TO_END_RUNBOOK.md" in README
    assert "docs/END_TO_END_RUNBOOK_DETAILED.md" in README
    assert "PROJECT_DEEP_DIVE.md" in README
    assert "not" in README.lower() and "production" in README.lower()
    assert "~~~powershell" not in README
    assert "END_TO_END_RUNBOOK.md" in (
        ROOT / "docs/release/README.md"
    ).read_text(encoding="utf-8")


def test_simple_guide_has_prerequisites_and_copy_paste_flows():
    assert GUIDE.index("Before you begin") < GUIDE.index("Step 1. Open PowerShell")
    assert "Step 2. Try everything" in GUIDE
    assert "-Flow all" in GUIDE
    assert "git clone https://github.com/" in GUIDE
    assert "cd agentic-engineering-toolkit" in GUIDE
    assert "PowerShell" in GUIDE
    assert "no credentials" in GUIDE.lower() or "no api key" in GUIDE.lower()
    for template in TEMPLATES:
        assert f"-Flow {template}" in GUIDE
        assert f'\"{template}\"' in RUNNER
    for flow in ("ingestion", "cloud-config", "ollama", "docker"):
        assert f"-Flow {flow}" in GUIDE
    assert DETAIL.is_file() and len(DETAIL.read_text(encoding="utf-8")) > len(GUIDE)
    assert "END_TO_END_RUNBOOK_DETAILED.md" in GUIDE


def test_real_demo_runner_preserves_isolation_and_strict_api_assertions():
    assert "& $AgentKit new" in RUNNER
    assert "& $AgentKit doctor" in RUNNER
    assert "py $PythonVersion -m venv" in RUNNER
    assert "-m pip check" in RUNNER
    assert "-m pytest -q" in RUNNER
    assert "127.0.0.1" in RUNNER
    assert "Invoke-RestMethod" in RUNNER
    assert "Stop-Process" in RUNNER
    assert "source_ids -notcontains" in RUNNER
    assert '"returns"' in RUNNER
    assert '"violet-manual"' in RUNNER
    assert "app.ingest" in RUNNER
    assert "tool_used" in RUNNER
    assert 'strands-agent' in RUNNER
    assert '$env:AET_PROVIDER = "mock"' in RUNNER
    assert '"cloud-config"' in RUNNER
    assert "No live model was called" in RUNNER
