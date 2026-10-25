"""Offline evaluation of AET-generated order workflow on user-supplied Olist CSV.

Do not distribute the Olist data; its official license is CC BY-NC-SA 4.0.
Only order_id and order_status are read. Results contain aggregates only.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import random
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ORDER_ID = re.compile(r"[0-9a-f]{32}\Z")
STATUSES = frozenset({
    "delivered", "shipped", "canceled", "unavailable",
    "invoiced", "processing", "created", "approved",
})
MAX_FILE_BYTES = 32_000_000
REQUIRED_MODULES = ("aet_scaffolder", "aet_quality", "fastapi", "langgraph", "httpx", "pydantic_settings")


class EvaluationError(ValueError):
    """Invalid evaluation input, runtime or result."""


def sample_orders(path: str | Path, *, limit: int = 200, seed: int = 19) -> tuple[dict[str, str], int]:
    """Uniform, seeded reservoir sample over the full orders file.

    Drops all customer, payment, location and timestamp columns immediately.
    IDs stay only in memory or temporary private process files, never reports.
    """
    if type(limit) is not int or not 1 <= limit <= 2000:
        raise EvaluationError("--sample must be between 1 and 2000")
    if type(seed) is not int or not 0 <= seed <= 2**32 - 1:
        raise EvaluationError("--seed must be a nonnegative 32-bit integer")
    file = Path(path).expanduser()
    try:
        if file.is_symlink() or not file.is_file():
            raise EvaluationError("CSV must be an ordinary local file (not a symlink)")
        if file.stat().st_size > MAX_FILE_BYTES:
            raise EvaluationError("CSV too large for local evaluation (>32MB)")
    except OSError as exc:
        raise EvaluationError("Unable to inspect the local CSV") from exc
    rng = random.Random(seed)
    selected: list[tuple[str, str]] = []
    seen_ids: set[str] = set()
    count = 0
    try:
        with file.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or not {"order_id", "order_status"}.issubset(reader.fieldnames):
                raise EvaluationError("Expected Olist columns: order_id and order_status")
            for line_number, row in enumerate(reader, start=2):
                oid = (row.get("order_id") or "").strip().lower()
                status = (row.get("order_status") or "").strip().lower()
                if not ORDER_ID.fullmatch(oid) or status not in STATUSES:
                    raise EvaluationError(f"Malformed ID or status on CSV line {line_number}")
                if oid in seen_ids:
                    raise EvaluationError(f"Duplicate order ID on CSV line {line_number}")
                seen_ids.add(oid)
                count += 1
                pair = (oid.upper(), status)
                if len(selected) < limit:
                    selected.append(pair)
                else:
                    position = rng.randrange(count)
                    if position < limit:
                        selected[position] = pair
    except (csv.Error, UnicodeError, OSError) as exc:
        raise EvaluationError("Unable to parse the local orders CSV") from exc
    if not selected:
        raise EvaluationError("Orders CSV contains no records")
    return dict(selected), count


def evaluate(path: str | Path, *, sample: int = 200, queries: int = 100, seed: int = 19,
             dataset_kind: str = "user_supplied_unverified") -> dict:
    if dataset_kind not in ("synthetic", "user_supplied_unverified"):
        raise EvaluationError("dataset_kind must be synthetic or user_supplied_unverified")
    if type(queries) is not int or not 1 <= queries <= 1000:
        raise EvaluationError("--queries must be between 1 and 1000")
    for module in REQUIRED_MODULES:
        if importlib.util.find_spec(module) is None:
            raise EvaluationError(f"Missing demo dependency: {module}; see docs/evaluation/README.md")
    from aet_scaffolder.generator import generate
    from aet_scaffolder.validator import validate_project

    orders, scanned = sample_orders(path, limit=sample, seed=seed)
    with tempfile.TemporaryDirectory(prefix="aet-olist-evaluation-") as tmp:
        project = generate("olist-eval", output_dir=tmp, provider="mock")
        report = validate_project(project)
        if not report.ok:
            raise EvaluationError("Generated project failed structural validation")
        evidence = Path(tmp) / "selected-orders.json"
        evidence.write_text(json.dumps(orders), encoding="utf-8")
        runner = Path(__file__).with_name("_olist_probe.py").resolve()
        env = os.environ.copy()
        env["AET_PROVIDER"] = "mock"
        env["PYTHONPATH"] = str(project)
        process = subprocess.run(
            [
                sys.executable, str(runner),
                "--records", str(evidence),
                "--queries", str(min(queries, len(orders))),
            ],
            env=env, cwd=project, check=False,
            text=True, capture_output=True, timeout=120,
        )
        if process.returncode:
            # Never print the subprocess output: it may contain order identifiers
            # from the locally supplied dataset.
            raise EvaluationError(f"Generated agent evaluation failed (exit {process.returncode})")
        try:
            result = json.loads(process.stdout)
        except ValueError as exc:
            raise EvaluationError("Evaluation subprocess did not return JSON") from exc
        if result.get("status") != "passed":
            raise EvaluationError("Evaluation subprocess reported a failure")
        if result.get("known_correct") != result.get("known_tested"):
            raise EvaluationError("Known-status correctness check failed")
        if result.get("unknown_correct") != result.get("unknown_tested"):
            raise EvaluationError("Unknown-order correctness check failed")
        return {
            "schema_version": 1,
            "status": "passed",
            "evaluation_type": "deterministic_generated_workflow_order_lookup",
            "source": "Olist-shaped local CSV supplied by evaluator (not authenticated)",
            "dataset_kind": dataset_kind,
            "license_notice": "Olist original: CC BY-NC-SA 4.0; check permissions for intended use",
            "records_scanned": scanned,
            "records_sampled": len(orders),
            "sample_seed": seed,
            "sample_status_distribution": dict(sorted(Counter(orders.values()).items())),
            "project_doctor_checks": len(report.checks),
            "metrics": result,
            "limitations": (
                "Offline historic order-status lookup only. No online order freshness, "
                "semantic LLM evaluation, live inference, developer time saving, "
                "human adoption or cloud-provider testing."
            ),
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate generated AET agent against local Olist orders CSV")
    parser.add_argument("--input", required=True, help="Path to local olist_orders_dataset.csv")
    parser.add_argument("--sample", type=int, default=200, help="Reservoir sample size (1-2000)")
    parser.add_argument("--queries", type=int, default=100, help="Positive lookup tests (1-1000)")
    parser.add_argument("--seed", type=int, default=19)
    parser.add_argument("--dataset-kind", choices=["synthetic", "user_supplied_unverified"],
                        default="user_supplied_unverified")
    parser.add_argument("--json-out", help="Write aggregate result to new JSON file; never overwrite")
    args = parser.parse_args(argv)
    try:
        if args.json_out and Path(args.json_out).exists():
            raise EvaluationError("Refusing to overwrite an existing report")
        result = evaluate(args.input, sample=args.sample, queries=args.queries,
                          seed=args.seed, dataset_kind=args.dataset_kind)
        output = json.dumps(result, indent=2, allow_nan=False) + "\n"
        if args.json_out:
            with Path(args.json_out).open("x", encoding="utf-8") as stream:
                stream.write(output)
        print(output, end="")
        return 0
    except (EvaluationError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"Olist evaluation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
