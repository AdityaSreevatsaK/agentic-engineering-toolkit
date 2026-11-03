"""Required CI must not depend on the optional external NYC 311 API."""
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[1]


def test_required_ci_uses_only_synthetic_nyc311_records():
    ci = (_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "evaluate_nyc311.py --synthetic-input" in ci
    assert "evaluate_nyc311.py --live" not in ci


def test_official_nyc311_check_requires_manual_dispatch():
    live = (_ROOT / ".github/workflows/nyc311-live.yml").read_text(
        encoding="utf-8"
    )
    assert "workflow_dispatch:" in live
    assert "pull_request:" not in live
    assert "push:" not in live
    assert "schedule:" not in live
    assert "evaluate_nyc311.py --live" in live
