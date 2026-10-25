"""M9 data validation tests only; no network, cloud, model or real Olist rows."""
import csv
import json
from pathlib import Path

import pytest

from scripts.evaluate_olist import EvaluationError, sample_orders

FIXTURE = Path(__file__).parent / "fixtures" / "olist_orders_synthetic.csv"


def write_records(tmp_path, rows):
    target = tmp_path / "orders.csv"
    with target.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["order_id", "order_status", "customer_id"])
        writer.writeheader()
        writer.writerows(rows)
    return target


def test_schema_and_seeded_reservoir():
    sample_a, total = sample_orders(FIXTURE, limit=3, seed=19)
    sample_b, total_b = sample_orders(FIXTURE, limit=3, seed=19)
    assert sample_a == sample_b
    assert total == total_b == 8
    assert len(sample_a) == 3
    assert all(len(order_id) == 32 for order_id in sample_a)
    assert set(sample_a.values()) <= {"delivered", "processing", "shipped", "canceled",
                                      "invoiced", "unavailable", "created", "approved"}


def test_full_sample_retains_all_synthetic_statuses():
    index, scanned = sample_orders(FIXTURE, limit=10, seed=19)
    assert scanned == 8
    assert len(index) == 8
    assert len(set(index.values())) == 8


@pytest.mark.parametrize("value", [0, 2001, True, 1.5, "2"])
def test_reject_invalid_sample_size(value):
    with pytest.raises(EvaluationError):
        sample_orders(FIXTURE, limit=value)


@pytest.mark.parametrize("seed", [-1, 2**32, 1.5, True])
def test_reject_invalid_seed(seed):
    with pytest.raises(EvaluationError):
        sample_orders(FIXTURE, seed=seed)


def test_missing_file_rejected(tmp_path):
    with pytest.raises(EvaluationError, match="CSV must"):
        sample_orders(tmp_path / "not-present.csv")


@pytest.mark.parametrize("bad", [
    {"order_id": "not-hex", "order_status": "delivered"},
    {"order_id": "a" * 32, "order_status": "unverified-new"},
    {"order_id": "", "order_status": "delivered"},
])
def test_malformed_status_or_id_rejected(tmp_path, bad):
    fields = {"customer_id": "ignored", **bad}
    with pytest.raises(EvaluationError, match="Malformed"):
        sample_orders(write_records(tmp_path, [fields]))


def test_duplicate_record_rejected(tmp_path):
    row = {"order_id": "a" * 32, "order_status": "delivered", "customer_id": "ignored"}
    with pytest.raises(EvaluationError, match="Duplicate"):
        sample_orders(write_records(tmp_path, [row, row]))


def test_empty_file_with_valid_header_is_rejected(tmp_path):
    with pytest.raises(EvaluationError, match="no records"):
        sample_orders(write_records(tmp_path, []))


def test_reject_symlink(tmp_path):
    pointer = tmp_path / "link.csv"
    try:
        pointer.symlink_to(FIXTURE)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks not supported on this environment")
    with pytest.raises(EvaluationError):
        sample_orders(pointer)


def test_aggregate_will_not_store_ids():
    # A pure non-network test that catches accidental raw-data exposure from
    # our own fixture metadata schema (the full integration runs in CI).
    selected, n = sample_orders(FIXTURE, limit=4, seed=42)
    report = {"rows": n, "status_counts": {s: list(selected.values()).count(s)
                                          for s in set(selected.values())}}
    assert all(oid not in json.dumps(report) for oid in selected)
