"""Pure contract checks for repeated sanitised local corpus race evidence."""
import json
from types import SimpleNamespace

import pytest

from scripts import stress_corpus_race as stress


def _synthetic_race(*, passed=True, non_200=0, writer_finished=True, swap_failed=False):
    return {"passed": passed, "events": [{
        "scenario": stress.SCENARIO,
        "passed": passed, "writer_completed": writer_finished,
        "atomic_replace_failed": swap_failed,
        "non_200_response_count": non_200,
        "raw_client_body": "SYNTHETIC-CANARY-DO-NOT-EXPORT",
    }]}


def test_bounded_corpus_stress_preserves_all_trials_and_no_raw_content(monkeypatch, tmp_path):
    created = []

    def generate(name, *, output_dir, template, provider):
        created.append((name, template, provider))
        return tmp_path / name

    responses = iter([
        _synthetic_race(),
        _synthetic_race(passed=False, non_200=2, writer_finished=False, swap_failed=True),
        _synthetic_race(),
    ])
    monkeypatch.setattr(stress, "generate", generate)
    monkeypatch.setattr(stress, "validate_project", lambda project: SimpleNamespace(ok=True))
    monkeypatch.setattr(stress, "run_pair", lambda *args: next(responses))
    result = stress.run_trials(3)
    assert result["trial_count"] == 3
    assert result["passed_trials"] == 2
    assert result["status"] == "fail"
    assert len(set(name for name, _, _ in created)) == 3
    assert all(template == "langgraph-rag" and provider == "openai"
               for _, template, provider in created)
    assert result["live_provider_called"] is False
    assert result["trials"][1]["non_200_response_count"] == 2
    assert result["trials"][1]["writer_completed"] is False
    assert result["trials"][1]["atomic_replace_failed"] is True
    assert "SYNTHETIC-CANARY-DO-NOT-EXPORT" not in json.dumps(result)


@pytest.mark.parametrize("trials", [0, -1, 21])
def test_corpus_stress_rejects_unsafe_trial_bounds(trials):
    with pytest.raises(ValueError, match="trials must be"):
        stress.run_trials(trials)


def test_corpus_stress_cli_does_not_overwrite_evidence(monkeypatch, tmp_path):
    path = tmp_path / "report.json"
    path.write_text("original", encoding="utf-8")
    monkeypatch.setattr(stress, "run_trials", lambda n: {
        "status": "pass", "trial_count": n, "passed_trials": n,
    })
    with pytest.raises(SystemExit):
        stress.main(["--trials", "2", "--json-out", str(path)])
    assert path.read_text(encoding="utf-8") == "original"
