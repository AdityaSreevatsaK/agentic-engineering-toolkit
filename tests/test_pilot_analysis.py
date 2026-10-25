"""All data here is synthetic: no measured pilot observations or people."""
import csv
import json
from pathlib import Path

import pytest

from scripts.analyze_pilot import COLUMNS, PilotDataError, analyze, main


def write_trials(tmp_path, rows):
    target = tmp_path / "trials.csv"
    with target.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return target


def row(code="synthetic-001", condition="manual", order="1", minutes="40",
        completed="yes", passed="yes", os="Windows", version="3.11"):
    return dict(participant_code=code, condition=condition, trial_order=order,
                active_minutes=minutes, completed=completed, tests_passed=passed,
                os=os, python_version=version)


def test_empty_template_must_not_claim_benefit(tmp_path):
    result = analyze(write_trials(tmp_path, []))
    assert result["status"] == "no_data"
    assert result["participants_recorded"] == 0
    assert result["condition_summary"]["manual"]["completion_rate_pct"] is None
    assert result["pair_summary"]["relative_median_reduction_pct"] is None


def test_exploratory_paired_comparison_is_explicit(tmp_path):
    rows = [
        row(minutes="40"), row(condition="toolkit", order="2", minutes="20"),
        row(code="synthetic-002", condition="toolkit", order="1", minutes="24"),
        row(code="synthetic-002", order="2", minutes="36"),
    ]
    report = analyze(write_trials(tmp_path, rows))
    assert report["status"] == "exploratory_only"
    assert report["participants_recorded"] == 2
    assert report["pair_summary"]["successful_comparable_pairs"] == 2
    assert report["pair_summary"]["matched_manual_median_minutes"] == 38
    assert report["pair_summary"]["matched_toolkit_median_minutes"] == 22
    assert report["pair_summary"]["relative_median_reduction_pct"] == 42.11
    assert report["pair_summary"]["order_counts"] == {"manual_first": 1, "toolkit_first": 1}
    serialized = json.dumps(report)
    assert "synthetic-001" not in serialized
    assert "synthetic-002" not in serialized


def test_failed_trials_are_never_counted_as_successful_pairs(tmp_path):
    rows = [
        row(completed="no", passed="no", minutes="120"),
        row(condition="toolkit", order="2", minutes="25"),
        row(code="synthetic-002", order="1", minutes="50"),
    ]
    report = analyze(write_trials(tmp_path, rows))
    assert report["total_attempts"] == 3
    assert report["pair_summary"]["paired_attempts"] == 1
    assert report["pair_summary"]["successful_comparable_pairs"] == 0
    assert report["pair_summary"]["paired_but_incomplete_or_failing"] == 1
    assert report["pair_summary"]["unpaired_participants"] == 1
    assert report["pair_summary"]["relative_median_reduction_pct"] is None
    assert report["condition_summary"]["manual"]["completion_rate_pct"] == 50


def test_minimum_pilot_count_needs_both_order_groups(tmp_path):
    rows = []
    for n in range(5):
        code = f"test-{n:03d}"
        manual_order = "1" if n % 2 == 0 else "2"
        toolkit_order = "2" if manual_order == "1" else "1"
        rows.append(row(code=code, order=manual_order, minutes="45"))
        rows.append(row(code=code, condition="toolkit", order=toolkit_order, minutes="35"))
    report = analyze(write_trials(tmp_path, rows))
    assert report["status"] == "pilot_data_ready_for_human_review"
    assert report["pair_summary"]["successful_comparable_pairs"] == 5
    assert report["pair_summary"]["relative_median_reduction_pct"] == 22.22
    assert "cannot establish causality" in report["caveats"][2]


def test_pilot_count_alone_does_not_replace_order_balance(tmp_path):
    rows = []
    for n in range(5):
        code = f"synthetic-{n:03d}"
        rows.extend([row(code=code), row(code=code, condition="toolkit", order="2")])
    assert analyze(write_trials(tmp_path, rows))["status"] == "exploratory_only"


@pytest.mark.parametrize("bad", [
    {"condition": "llm"},
    {"trial_order": "3"},
    {"active_minutes": "-4"},
    {"active_minutes": "nan"},
    {"active_minutes": "inf"},
    {"active_minutes": "121"},
    {"completed": "maybe"},
    {"tests_passed": "maybe"},
    {"completed": "no", "tests_passed": "yes"},
    {"participant_code": "someone@example.com"},
    {"os": "cloud"},
    {"python_version": "3.7"},
])
def test_invalid_input_rejected(tmp_path, bad):
    fields = dict(row())
    fields.update(bad)
    with pytest.raises(PilotDataError):
        analyze(write_trials(tmp_path, [fields]))


def test_duplicate_condition_rejected(tmp_path):
    with pytest.raises(PilotDataError, match="Duplicate"):
        analyze(write_trials(tmp_path, [row(), row(minutes="38")]))


def test_paired_trial_order_must_differ(tmp_path):
    with pytest.raises(PilotDataError, match="trial_order"):
        analyze(write_trials(tmp_path, [row(), row(condition="toolkit", order="1")]))


def test_paired_python_or_os_mismatch_rejected(tmp_path):
    with pytest.raises(PilotDataError, match="same OS"):
        analyze(write_trials(tmp_path, [
            row(), row(condition="toolkit", order="2", version="3.12"),
        ]))


def test_reject_wrong_header_and_extra_values(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("email,condition\nprivate@example.com,manual\n", encoding="utf-8")
    with pytest.raises(PilotDataError, match="header"):
        analyze(bad)


def test_cli_supports_empty_template_without_overwrite(tmp_path, capsys):
    source = write_trials(tmp_path, [])
    target = tmp_path / "aggregates.json"
    args = ["--input", str(source), "--json-out", str(target)]
    assert main(args) == 0
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["status"] == "no_data"
    assert main(args) == 2
    assert json.loads(target.read_text(encoding="utf-8")) == payload


def test_missing_trial_file_is_rejected(tmp_path):
    with pytest.raises(PilotDataError, match="Cannot read"):
        analyze(tmp_path / "not-found.csv")
