"""Required CI must not depend on the optional external NYC 311 API."""
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[1]


def test_required_ci_uses_only_synthetic_nyc311_records():
    ci = (_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "evaluate_nyc311.py --synthetic-input" in ci
    assert "evaluate_nyc311.py --live" not in ci


def test_retired_external_nyc311_workflow_cannot_reenter_required_ci():
    """Keep historical M10 evidence but do not run external API calls in CI."""
    assert not (_ROOT / ".github/workflows/nyc311-live.yml").exists()
    for name in ("ci.yml", "dependency-audit.yml"):
        workflow = (_ROOT / ".github/workflows" / name).read_text(
            encoding="utf-8"
        )
        assert "evaluate_nyc311.py --live" not in workflow
