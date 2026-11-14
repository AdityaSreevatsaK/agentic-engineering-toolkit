"""Deep event sweep must be complete, safe, and leave only sanitised evidence."""
import ast
import json
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from aet_scaffolder.registry import SUPPORTED_TEMPLATES, get_template
from scripts import deep_event_matrix as audit


def test_deep_event_enumeration_matches_registry():
    pairs = audit.supported_pairs()
    assert len(pairs) == 23
    assert len(set(pairs)) == len(pairs)
    assert {item for item, _ in pairs} == set(SUPPORTED_TEMPLATES)
    for template in SUPPORTED_TEMPLATES:
        assert {provider for item, provider in pairs if item == template} == set(
            get_template(template).providers
        )


def test_required_scenarios_include_hostile_inputs_and_rag_state_transitions():
    assert len(audit.SCENARIOS) >= 25
    assert len(audit.RAG_SCENARIOS) >= 6
    assert audit.SECURITY_SCENARIOS <= set(audit.SCENARIOS)
    for required in (
        "malformed_json", "one_mib_question", "parallel_burst",
        "secret_header_canary", "sanitised_exception",
    ):
        assert required in audit.SCENARIOS


def test_statistical_quantiles_are_interpolated_and_empty_safe():
    assert audit.percentile([], 0.95) == 0
    assert audit.percentile([10, 20, 30], 0.5) == 20
    assert audit.percentile([10, 20, 30], 0.95) == 29


def test_child_probes_require_unique_full_scenario_coverage(monkeypatch, tmp_path):
    class StubProcess:
        returncode = 0
        stdout = audit.MARKER + json.dumps({
            "passed": True, "count": 1,
            "events": [{"scenario": "health", "passed": True}],
        })
    monkeypatch.setattr(audit.subprocess, "run", lambda *args, **kwargs: StubProcess())
    result = audit.run_pair("tool-agent", "mock", tmp_path)
    assert not result["passed"]
    assert result["failure_stage"] == "incomplete_scenarios"


def test_child_probe_strips_host_credentials(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-secret-do-not-pass")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "synthetic-secret-do-not-pass")

    class StubProcess:
        returncode = 1
        stdout = ""
    def stub_run(*args, **kwargs):
        assert "OPENAI_API_KEY" not in kwargs["env"]
        assert "AWS_SECRET_ACCESS_KEY" not in kwargs["env"]
        assert kwargs["env"]["AET_PROVIDER"] == "mock"
        assert kwargs["timeout"] <= 180
        return StubProcess()
    monkeypatch.setattr(audit.subprocess, "run", stub_run)
    assert audit.run_pair("tool-agent", "mock", tmp_path)["failure_stage"] == "probe_failed"


def test_report_cli_refuses_to_overwrite_existing_evidence(tmp_path):
    existing = tmp_path / "present.json"
    existing.write_text("do not overwrite", encoding="utf-8")
    with pytest.raises(SystemExit):
        audit.main([
            "--json-out", str(existing),
            "--csv-out", str(tmp_path / "metrics.csv"),
            "--failures-out", str(tmp_path / "failures.jsonl"),
            "--security-out", str(tmp_path / "security.json"),
        ])
    assert existing.read_text(encoding="utf-8") == "do not overwrite"


def test_can_create_machine_readable_artifacts_without_running_cloud(monkeypatch, tmp_path):
    expected = ({"schema_version": 1, "status": "pass", "pair_count": 1,
                 "passed_pairs": 1, "scenario_count": 28,
                 "passed_scenarios": 28, "environment": {},
                 "evidence_type": audit.EVIDENCE_TYPE},
                [], [], {"schema_version": 1, "status": "pass"})
    monkeypatch.setattr(audit, "run_matrix", lambda: expected)
    paths = [tmp_path / filename for filename in
             ("result.json", "metrics.csv", "errors.jsonl", "security.json")]
    assert audit.main([
        "--json-out", str(paths[0]), "--csv-out", str(paths[1]),
        "--failures-out", str(paths[2]), "--security-out", str(paths[3]),
    ]) == 0
    assert json.loads(paths[0].read_text())["status"] == "pass"
    assert paths[1].read_text().startswith("template,")
    assert paths[2].read_text() == ""
    assert json.loads(paths[3].read_text())["status"] == "pass"


def _extract_child_atomic_update(*, os_module, pause):
    """Exercise the actual stdlib writer embedded in the isolated child script."""
    tree = ast.parse(audit._CHILD)
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "atomic_update"
    )
    namespace = {
        "tempfile": tempfile, "Path": Path, "os": os_module, "sleep": pause,
    }
    exec(compile(ast.Module(body=[function], type_ignores=[]),
                 "<synthetic-writer-test>", "exec"), namespace)
    return namespace["atomic_update"]


def test_windows_atomic_writer_retries_then_publishes_complete_content(tmp_path):
    path = tmp_path / "knowledge.jsonl"
    path.write_bytes(b"original\n")
    attempted = []
    sleeps = []

    def replace(source, target):
        attempted.append(1)
        if len(attempted) <= 3:
            raise PermissionError("synthetic-locked-file")
        os.replace(source, target)

    update = _extract_child_atomic_update(
        os_module=SimpleNamespace(name="nt", replace=replace),
        pause=sleeps.append,
    )
    update(path, b"updated\n")
    assert path.read_bytes() == b"updated\n"
    assert len(attempted) == 4
    assert sleeps == [0.01] * 3
    assert sorted(tmp_path.iterdir()) == [path]


def test_windows_atomic_writer_fails_closed_after_bounded_denials(tmp_path):
    path = tmp_path / "knowledge.jsonl"
    path.write_bytes(b"original\n")
    attempts = []
    delays = []

    def deny(source, target):
        attempts.append(1)
        raise PermissionError("synthetic-permanent-denial")

    update = _extract_child_atomic_update(
        os_module=SimpleNamespace(name="nt", replace=deny),
        pause=delays.append,
    )
    with pytest.raises(PermissionError, match="synthetic-permanent-denial"):
        update(path, b"never-published\n")
    assert path.read_bytes() == b"original\n"
    assert len(attempts) == 100
    assert delays == [0.01] * 99
    assert sorted(tmp_path.iterdir()) == [path]


def test_non_windows_atomic_writer_does_not_retry_permissions(tmp_path):
    path = tmp_path / "knowledge.jsonl"
    path.write_bytes(b"original\n")
    attempts = []
    delays = []

    def deny(source, target):
        attempts.append(1)
        raise PermissionError("synthetic-permission-denied")

    update = _extract_child_atomic_update(
        os_module=SimpleNamespace(name="posix", replace=deny),
        pause=delays.append,
    )
    with pytest.raises(PermissionError):
        update(path, b"new\n")
    assert len(attempts) == 1
    assert delays == []
    assert path.read_bytes() == b"original\n"
    assert sorted(tmp_path.iterdir()) == [path]


def test_race_failures_report_only_allowlisted_categorical_diagnostics(monkeypatch):
    monkeypatch.setattr(audit, "supported_pairs", lambda: [("langgraph-rag", "openai")])
    monkeypatch.setattr(audit, "generate", lambda *args, **kwargs: Path("synthetic"))
    monkeypatch.setattr(audit, "validate_project", lambda project: SimpleNamespace(ok=True))

    def failed_pair(*args):
        return {
            "passed": False, "count": 1, "passed_count": 0,
            "events": [{
                "scenario": "concurrent_atomic_corpus_updates",
                "status_code": 503, "passed": False,
                "writer_completed": True, "atomic_replace_failed": True,
                "non_200_response_count": 2,
                "non_200_http_statuses": [503, 500, 200, 999, "NEVER-EXPORT-SECRET"],
                "synthetic_raw_exception": "NEVER-EXPORT-SECRET",
            }],
        }

    monkeypatch.setattr(audit, "run_pair", failed_pair)
    report, rows, failures, security = audit.run_matrix()
    assert report["status"] == "fail"
    assert rows[0]["status_code"] == 503
    assert failures == [{
        "template": "langgraph-rag", "provider": "openai",
        "scenario": "concurrent_atomic_corpus_updates",
        "status_code": 503, "failure_stage": "event_assertion",
        "race_diagnostics": {
            "writer_completed": True,
            "atomic_replace_failed": True,
            "non_200_response_count": 2,
            "non_200_http_statuses": [500, 503],
        },
    }]
    assert "NEVER-EXPORT-SECRET" not in json.dumps(failures)
    assert security["status"] == "fail"
