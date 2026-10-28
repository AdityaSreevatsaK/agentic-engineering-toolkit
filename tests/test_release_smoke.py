"""M19 machine-only four-template release smoke contracts."""
import json
from pathlib import Path
from types import SimpleNamespace

from aet_scaffolder.registry import SUPPORTED_TEMPLATES
from scripts import release_smoke


def _fake_probe(project, template):
    assert Path(project).is_dir()
    assert template in SUPPORTED_TEMPLATES
    return {
        "health_ok": True,
        "ready_ok": True,
        "initial_api_ok": True,
        "invalid_request_rejected": True,
        "corpus_change_ok": True if template in {"langgraph-rag", "llamaindex-rag"} else None,
    }


def test_machine_smoke_generates_and_doctor_checks_all_templates(monkeypatch):
    monkeypatch.setattr(release_smoke, "_probe_project", _fake_probe)
    report = release_smoke.run_release_smoke()
    assert report["status"] == "pass"
    assert report["evidence_type"] == "automated_local_application_smoke"
    assert {x["template"] for x in report["results"]} == set(SUPPORTED_TEMPLATES)
    assert all(x["passed"] and x["generated"] and x["doctor_ok"]
               for x in report["results"])
    assert all(x["corpus_change_ok"] is True for x in report["results"]
               if x["template"].endswith("-rag"))
    assert report["independent_human_trial"] is False
    assert report["multi_team_adoption_verified"] is False
    assert report["live_provider_verified"] is False
    assert report["human_time_saved"] is None
    assert "machine" in report["machine_timing_scope"] or "human" in report["machine_timing_scope"]


def test_http_failure_is_recorded_without_raw_error(monkeypatch):
    def failed_probe(*args):
        raise RuntimeError("Secret: sample-api-key and private host details")
    monkeypatch.setattr(release_smoke, "_probe_project", failed_probe)
    report = release_smoke.run_release_smoke()
    assert report["status"] == "fail"
    assert all(x["failure_stage"] == "api_probe" for x in report["results"])
    assert "sample-api-key" not in json.dumps(report)
    assert all(not x["passed"] for x in report["results"])


def test_report_is_written_exclusively_and_not_overwritten(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(release_smoke, "_probe_project", _fake_probe)
    target = tmp_path / "machine-report.json"
    assert release_smoke.main(["--json-out", str(target)]) == 0
    original = target.read_text(encoding="utf-8")
    data = json.loads(original)
    assert data["status"] == "pass"
    assert len(data["results"]) == len(SUPPORTED_TEMPLATES)
    assert release_smoke.main(["--json-out", str(target)]) == 2
    assert target.read_text(encoding="utf-8") == original


def test_child_env_does_not_inherit_cloud_secrets(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret-1")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret-2")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret-3")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "secret-4")
    monkeypatch.setenv("AET_PROVIDER", "bedrock")
    env = release_smoke._clean_environment()
    assert env["AET_PROVIDER"] == "mock"
    assert env["AET_KNOWLEDGE_PATH"] == "data/knowledge.jsonl"
    assert not any("secret" in value for value in env.values())
    assert not any("API_KEY" in name for name in env)


def test_reject_nonzero_child_exit_without_leaking_output(monkeypatch, tmp_path):
    monkeypatch.setattr(
        release_smoke.subprocess, "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1, stdout="api-key leaked", stderr="private path leaked"
        ),
    )
    try:
        release_smoke._probe_project(tmp_path, "tool-agent")
    except RuntimeError as exc:
        assert str(exc) == "api_probe_failed"
    else:
        assert False, "expected a sanitised failure"
