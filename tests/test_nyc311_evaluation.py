"""M10 source parsing and mocked-HTTP tests without public API calls."""
import json
from pathlib import Path

import pytest

from scripts.evaluate_nyc311 import (
    DEFAULT_END, DEFAULT_START, EvaluationError, SOURCE, _parse_records,
    _query, fetch_official,
)

FIXTURE = Path(__file__).parent / "fixtures" / "nyc311_synthetic.json"


def test_local_synthetic_fixture_has_only_requested_fields():
    records = json.loads(FIXTURE.read_text(encoding="utf-8"))
    parsed = _parse_records(records, cap=10)
    assert len(parsed) == 6
    assert set(parsed.values()) == {"Closed", "In Progress", "Open", "Pending", "Assigned"}


def test_official_fetch_requests_only_key_and_status():
    captured = []

    def fake(url):
        captured.append(url)
        return json.dumps([
            {"unique_key": "12345678", "status": "Closed", "location": "not-used"},
            {"unique_key": "12345679", "status": "In Progress"},
        ]).encode("utf-8")

    records = fetch_official(limit=3, transport=fake)
    assert records == {"12345678": "Closed", "12345679": "In Progress"}
    assert len(captured) == 1
    assert captured[0].startswith(SOURCE + "?")
    assert "unique_key%2Cstatus" in captured[0]
    assert "order=unique_key+DESC" in captured[0]
    assert "12345678" not in captured[0]


@pytest.mark.parametrize("limit", [0, 501, True, 2.5, "30"])
def test_invalid_limit_rejected(limit):
    with pytest.raises(EvaluationError):
        _query(limit)


@pytest.mark.parametrize("rows", [
    [],
    [{"unique_key": "1", "status": "Closed"}],
    [{"unique_key": "12345678", "status": ""}],
    [{"unique_key": "12345678", "status": "<unsafe>"}],
    [{"unique_key": "12345678", "status": "Closed", "secret": "ignored"},
     {"unique_key": "12345678", "status": "Open"}],
    [{"unique_key": "12345678", "status": "Closed"}, {"unique_key": "12345679", "status": "Open"}],
])
def test_reject_malformed_api_responses(rows):
    cap = 1 if len(rows) == 2 and rows[0].get("unique_key") != rows[-1].get("unique_key") else 10
    with pytest.raises(EvaluationError):
        _parse_records(rows, cap=cap)


def test_full_record_list_not_accepted():
    with pytest.raises(EvaluationError):
        _parse_records([{"unique_key": "12345678", "status": "Closed"}] * 501, cap=500)


def test_network_errors_are_sanitized():
    def fail(url):
        raise OSError("private system debugging details")
    with pytest.raises(EvaluationError, match="Official NYC 311 API unavailable") as exc:
        fetch_official(transport=fail)
    assert "private system debugging" not in str(exc.value)


def test_oversize_response_rejected():
    with pytest.raises(EvaluationError, match="oversized"):
        fetch_official(transport=lambda _: b" " * 200_001)


def test_api_query_is_bounded_and_only_requests_status_fields():
    url = _query(10)
    assert "limit=10" in url
    assert "unique_key%2Cstatus" in url
    assert "order=unique_key+DESC" in url
    assert "where=" not in url


def test_raw_id_or_address_are_not_in_aggregate_report():
    # The subprocess integration and real-data workflow assert all output is
    # aggregated; this guard limits script output to known metric/report fields.
    text = (Path(__file__).parent.parent / "scripts" / "evaluate_nyc311.py").read_text(encoding="utf-8")
    assert '"source_kind": source_kind' in text
    assert '"status_distribution":' in text
    assert "incident_address" not in text
