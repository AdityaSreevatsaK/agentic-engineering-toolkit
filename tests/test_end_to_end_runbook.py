"""Prevent the public end-to-end runbook drifting from AET's template registry.

This is a documentation contract check, not a substitute for the real
four-platform generated-app and mock HTTP tests in GitHub Actions.
"""
from pathlib import Path

from aet_scaffolder.registry import TEMPLATES


ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = (ROOT / "docs" / "END_TO_END_RUNBOOK.md").read_text(encoding="utf-8")


def test_every_registered_template_has_complete_generation_and_http_flow():
    for template, spec in TEMPLATES.items():
        assert f'-Template "{template}"' in RUNBOOK
        assert f'"demo-{template}"' in RUNBOOK
        path = ROOT / "src" / "aet_scaffolder" / "templates" / spec.directory / "app" / "main.py"
        app_source = path.read_text(encoding="utf-8")
        endpoint = "/ask" if template.endswith("-rag") else "/invoke"
        assert f'@app.post("{endpoint}"' in app_source
        assert endpoint in RUNBOOK
    assert "New-VerifiedAetProject" in RUNBOOK
    assert "Start-AetLocalServer" in RUNBOOK
    assert "-m pip check" in RUNBOOK
    assert "-m pytest -q" in RUNBOOK
    assert "Stop-Process -Id $Server.Id" in RUNBOOK


def test_rag_flows_demonstrate_real_corpus_mutation_and_retrieval():
    assert RUNBOOK.count("Add-Content -LiteralPath $Corpus") >= 2
    assert RUNBOOK.count('source_ids -notcontains "returns"') >= 2
    assert RUNBOOK.count('source_ids -notcontains "violet-manual"') >= 2
    assert "app.ingest --input synthetic-documents" in RUNBOOK
    assert "AET_KNOWLEDGE_PATH" in RUNBOOK


def test_readme_and_release_kit_link_the_executable_runbook():
    assert "docs/END_TO_END_RUNBOOK.md" in (ROOT / "README.md").read_text(encoding="utf-8")
    assert "../END_TO_END_RUNBOOK.md" in (
        ROOT / "docs" / "release" / "README.md"
    ).read_text(encoding="utf-8")
    assert "scripts.isolated_install_smoke" in RUNBOOK
    assert "windows-2025, 3.12" in RUNBOOK
    assert "no credentials" in RUNBOOK.lower()
