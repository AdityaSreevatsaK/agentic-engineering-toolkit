"""NYC 311 public-data agent benchmark: real API opt-in, synthetic tests by default.

Only public request IDs and statuses are transferred to the temporary workspace.
No location, complaint text, contact information or full records are retained.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SOURCE = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"
DATASET = "311 Service Requests from 2020 to Present"
SOURCE_PAGE = "https://data.cityofnewyork.us/d/erm2-nwe9"
DEFAULT_START = "2025-01-01T00:00:00"
DEFAULT_END = "2025-02-01T00:00:00"
KEY = re.compile(r"[0-9]{6,12}\Z")
DEPS = ("aet_scaffolder", "aet_quality", "fastapi", "langgraph", "httpx", "pydantic_settings")
MAX_RESPONSE = 200_000


class EvaluationError(ValueError):
    """Bounded evaluation input or execution was not valid."""


def _parse_records(value: object, *, cap: int) -> dict[str, str]:
    if not isinstance(value, list) or not value or len(value) > cap:
        raise EvaluationError("Expected a nonempty bounded list of public 311 records")
    result: dict[str, str] = {}
    for record in value:
        if not isinstance(record, dict):
            raise EvaluationError("Invalid source record type")
        key, status = record.get("unique_key"), record.get("status")
        if not isinstance(key, str) or not KEY.fullmatch(key):
            raise EvaluationError("Source record has invalid numeric request ID")
        if not isinstance(status, str) or not status.strip() or len(status) > 120:
            raise EvaluationError("Source record has invalid status")
        clean = status.strip()
        # Keep only a bounded alphanumeric status label; never accept arbitrary
        # complaint text or personal details in an output string.
        if not re.fullmatch(r"[A-Za-z][A-Za-z _/-]{0,119}", clean):
            raise EvaluationError("Source status has unexpected characters")
        if key in result:
            raise EvaluationError("Source returned duplicate request IDs")
        result[key] = clean
    return result


def _query(limit: int) -> str:
    if type(limit) is not int or not 1 <= limit <= 500:
        raise EvaluationError("--limit must be an integer from 1 to 500")
    options = {
        "$select": "unique_key,status",
        "$where": (
            f"created_date >= '{DEFAULT_START}' "
            f"AND created_date < '{DEFAULT_END}' AND status IS NOT NULL"
        ),
        "$order": "unique_key DESC",
        "$limit": str(limit),
    }
    return SOURCE + "?" + urlencode(options)


def fetch_official(limit: int = 120, *, transport=None) -> dict[str, str]:
    """Read solely two fields from NYC's official Socrata API.

    Callers may inject an offline response to unit-test parsing without egress.
    """
    url = _query(limit)
    if transport is None:
        def transport(uri):
            request = Request(uri, headers={"Accept": "application/json", "User-Agent": "AET-public-data-eval/0.1"})
            with urlopen(request, timeout=25) as response:
                return response.read(MAX_RESPONSE + 1)
    try:
        raw = transport(url)
    except (OSError, TimeoutError) as exc:
        raise EvaluationError("Official NYC 311 API unavailable") from exc
    if not isinstance(raw, bytes) or len(raw) > MAX_RESPONSE:
        raise EvaluationError("Official API returned an oversized or invalid payload")
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise EvaluationError("Official API did not return valid JSON") from exc
    return _parse_records(decoded, cap=limit)


def evaluate(
    records: dict[str, str],
    *,
    source_kind: str,
    query_count: int = 100,
    retrieved_utc: str | None = None,
) -> dict:
    if source_kind not in ("nyc311_official_live", "synthetic", "user_supplied_unverified"):
        raise EvaluationError("Unrecognized source_kind")
    if type(query_count) is not int or not 1 <= query_count <= 500:
        raise EvaluationError("--queries must be an integer from 1 to 500")
    clean = _parse_records(
        [{"unique_key": k, "status": v} for k, v in records.items()],
        cap=500,
    )
    for module in DEPS:
        if importlib.util.find_spec(module) is None:
            raise EvaluationError(f"Missing dependency: {module}; see docs/evaluation/nyc311.md")
    from aet_scaffolder.generator import generate
    from aet_scaffolder.validator import validate_project

    with tempfile.TemporaryDirectory(prefix="aet-nyc311-") as temp:
        project = generate("nyc311-eval", output_dir=temp, provider="mock")
        doctor = validate_project(project)
        if not doctor.ok:
            raise EvaluationError("Generated application failed static validation")

        local = Path(temp) / "selected-requests.json"
        local.write_text(json.dumps(clean, ensure_ascii=True), encoding="utf-8")
        script = Path(__file__).with_name("_nyc311_probe.py").resolve()
        env = os.environ.copy()
        env["AET_PROVIDER"] = "mock"
        env["PYTHONPATH"] = str(project)
        result = subprocess.run(
            [sys.executable, str(script), "--input", str(local),
             "--queries", str(min(query_count, len(clean)))],
            cwd=project, env=env, text=True, capture_output=True, timeout=90,
            check=False,
        )
        if result.returncode:
            # Do not expose captured text or public request IDs in CI logs.
            raise EvaluationError(f"Agent status probe failed (exit {result.returncode})")
        try:
            measured = json.loads(result.stdout)
        except ValueError as exc:
            raise EvaluationError("Agent status probe returned invalid metrics") from exc
        if measured.get("status") != "passed" or measured.get("known_tested") != measured.get("known_correct"):
            raise EvaluationError("Agent status evaluation was not successful")

        # Nonreversible integrity fingerprint over public ID/status pairs, not
        # raw records; allows comparisons between samples without storing IDs.
        fingerprint = hashlib.sha256(
            json.dumps(sorted(clean.items()), separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        from collections import Counter
        return {
            "schema_version": 1,
            "status": "passed",
            "dataset_name": DATASET if source_kind == "nyc311_official_live" else "NYC311-format records",
            "source_kind": source_kind,
            "source_page": SOURCE_PAGE,
            "source_api": SOURCE,
            "source_query_period_utc": [DEFAULT_START, DEFAULT_END] if source_kind == "nyc311_official_live" else None,
            "retrieved_utc": retrieved_utc,
            "record_count": len(clean),
            "sample_fingerprint_sha256": fingerprint,
            "status_distribution": dict(sorted(__import__("collections").Counter(clean.values()).items())),
            "static_checks_passed": len(doctor.checks),
            "measurements": measured,
            "data_handling": "Only request IDs and status labels used in temporary process. Aggregate report contains no raw rows or identifiers.",
            "limitations": (
                "Deterministic in-process lookup, not live 311 system, semantic LLM model, "
                "production API latency, developer productivity, cloud parity or team adoption."
            ),
        }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Benchmark generated agent against official NYC 311 statuses")
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--live", action="store_true", help="Fetch official NYC Open Data API (network required)")
    source.add_argument("--synthetic-input", help="Explicitly label controlled local fixture as synthetic")
    p.add_argument("--limit", type=int, default=120)
    p.add_argument("--queries", type=int, default=100)
    p.add_argument("--json-out", help="Write aggregate-only report to a NEW file")
    args = p.parse_args(argv)
    try:
        if args.json_out and Path(args.json_out).exists():
            raise EvaluationError("Refusing to overwrite an existing report")
        if args.live:
            data = fetch_official(limit=args.limit)
            kind = "nyc311_official_live"
            retrieved_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
        else:
            path = Path(args.synthetic_input)
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 200_000:
                raise EvaluationError("Synthetic input must be a small ordinary local file")
            data = _parse_records(json.loads(path.read_text(encoding="utf-8")), cap=500)
            kind = "synthetic"
            retrieved_utc = None
        metrics = evaluate(data, source_kind=kind, query_count=args.queries, retrieved_utc=retrieved_utc)
        rendered = json.dumps(metrics, indent=2, allow_nan=False) + "\n"
        if args.json_out:
            with Path(args.json_out).open("x", encoding="utf-8") as handle:
                handle.write(rendered)
        print(rendered, end="")
        return 0
    except (EvaluationError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"NYC 311 evaluation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
