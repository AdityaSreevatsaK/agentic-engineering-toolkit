"""M4 timings are observation only, not a proof of productivity gains."""
import csv
import json

import pytest

from aet_scaffolder.benchmark import run
from aet_scaffolder.benchmark_cli import main


@pytest.mark.parametrize("provider", ["mock", "ollama"])
def test_microbenchmark_measures_only_successful_runs(provider):
    result = run(runs=3, warmups=1, provider=provider)
    assert result["runs"] == 3
    assert result["warmups"] == 1
    assert len(result["samples"]) == 3
    assert result["provider"] == provider
    for measure in ("generation_ms", "validation_ms", "total_ms"):
        assert result["summary"][measure]["median_ms"] >= 0
        assert result["summary"][measure]["p95_ms"] >= 0
    assert "not developer time saved" in result["scope"]


@pytest.mark.parametrize("options", [{"runs": 0}, {"runs": 51}, {"warmups": -1}, {"warmups": 11}])
def test_reject_unsafe_run_counts(options):
    with pytest.raises(ValueError):
        run(**options)


def test_cli_emits_json_csv_and_no_overwrite(tmp_path, capsys):
    json_path = tmp_path / "timings.json"
    csv_path = tmp_path / "timings.csv"
    args = ["--runs", "2", "--warmups", "0", "--json-out", str(json_path), "--csv-out", str(csv_path)]
    assert main(args) == 0
    data = json.loads(json_path.read_text())
    assert len(data["samples"]) == 2
    with csv_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 2
    assert main(args) == 2
    assert json.loads(json_path.read_text()) == data


def test_cli_rejects_colliding_paths(tmp_path):
    path = str(tmp_path / "same.json")
    assert main(["--runs", "1", "--json-out", path, "--csv-out", path]) == 2
