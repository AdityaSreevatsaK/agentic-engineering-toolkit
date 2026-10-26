"""M15 preflight never invents human pilot or developer-time claims."""
import json

from scripts import adoption_preflight


def test_offline_preflight_checks_three_templates():
    result = adoption_preflight.run_preflight()
    assert result["status"] == "pass"
    assert result["evidence_type"] == "automated_structural_preflight"
    assert result["independent_human_trial"] is False
    assert result["human_time_saved"] is None
    assert result["live_provider_verified"] is False
    assert {x["template"] for x in result["results"]} == {
        "tool-agent", "langgraph-rag", "strands-agent"
    }
    assert all(x["passed"] for x in result["results"])


def test_cli_writes_new_non_sensitive_report_and_does_not_overwrite(tmp_path, capsys):
    path = tmp_path / "machine-report.json"
    assert adoption_preflight.main(["--json-out", str(path)]) == 0
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["status"] == "pass"
    assert "participant" not in json.dumps(report).lower()
    first = path.read_text(encoding="utf-8")
    assert adoption_preflight.main(["--json-out", str(path)]) == 2
    assert path.read_text(encoding="utf-8") == first


def test_detects_failure_without_reporting_human_adoption(monkeypatch):
    class FailedDoctor:
        ok = False

    monkeypatch.setattr(adoption_preflight, "validate_project", lambda path: FailedDoctor())
    report = adoption_preflight.run_preflight()
    assert report["status"] == "fail"
    assert report["independent_human_trial"] is False
    assert all(not x["passed"] for x in report["results"])


def test_missing_out_parent_is_reported_without_creating_directories(tmp_path):
    dest = tmp_path / "not-created" / "report.json"
    assert adoption_preflight.main(["--json-out", str(dest)]) == 2
    assert not dest.parent.exists()
