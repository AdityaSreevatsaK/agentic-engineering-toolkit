"""Analyze consented, pseudonymized AET setup trials locally.

No data is transmitted. No participant identifiers or free-text fields appear in
the aggregate report. Empty templates produce an explicit no-data result.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

COLUMNS = (
    "participant_code", "condition", "trial_order", "active_minutes",
    "completed", "tests_passed", "os", "python_version",
)
CODE = re.compile(r"[A-Za-z0-9_-]{1,24}\Z")
VERSION = re.compile(r"3\.(11|12)\Z")
YES_NO = {"yes": True, "no": False}


class PilotDataError(ValueError):
    """Input is incomplete, inconsistent or unsafe to interpret."""


def _load(path: Path) -> list[dict]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != COLUMNS:
                raise PilotDataError("CSV header must match docs/pilot/trials-template.csv exactly")
            rows = []
            for line, raw in enumerate(reader, start=2):
                if None in raw or any(value is None for value in raw.values()):
                    raise PilotDataError(f"Line {line}: incorrect number of fields")
                record = {key: value.strip() for key, value in raw.items()}
                code = record["participant_code"]
                if not CODE.fullmatch(code):
                    raise PilotDataError(f"Line {line}: participant_code must be an anonymous short code")
                if record["condition"] not in ("manual", "toolkit"):
                    raise PilotDataError(f"Line {line}: condition must be manual or toolkit")
                if record["trial_order"] not in ("1", "2"):
                    raise PilotDataError(f"Line {line}: trial_order must be 1 or 2")
                try:
                    minutes = float(record["active_minutes"])
                except ValueError as exc:
                    raise PilotDataError(f"Line {line}: invalid active_minutes") from exc
                if not math.isfinite(minutes) or not (0 < minutes <= 120):
                    raise PilotDataError(f"Line {line}: active_minutes must be >0 and <=120")
                if record["completed"] not in YES_NO or record["tests_passed"] not in YES_NO:
                    raise PilotDataError(f"Line {line}: completed/tests_passed must be yes or no")
                if record["tests_passed"] == "yes" and record["completed"] != "yes":
                    raise PilotDataError(f"Line {line}: tests cannot pass for an incomplete trial")
                if record["os"] not in ("Windows", "Linux", "macOS"):
                    raise PilotDataError(f"Line {line}: OS must be Windows, Linux or macOS")
                if not VERSION.fullmatch(record["python_version"]):
                    raise PilotDataError(f"Line {line}: use Python 3.11 or 3.12")
                record["active_minutes"] = minutes
                record["successful"] = record["completed"] == "yes" and record["tests_passed"] == "yes"
                rows.append(record)
            return rows
    except OSError as exc:
        raise PilotDataError(f"Cannot read trial CSV: {exc.strerror or type(exc).__name__}") from exc


def _median(values: list[float]) -> float | None:
    return round(statistics.median(values), 2) if values else None


def analyze(path: str | Path) -> dict:
    """Return aggregate measurements only. Do not extrapolate from missing trials."""
    rows = _load(Path(path))
    participants: dict[str, dict[str, dict]] = {}
    for row in rows:
        code, condition = row["participant_code"], row["condition"]
        by_person = participants.setdefault(code, {})
        if condition in by_person:
            raise PilotDataError("Duplicate condition for the same anonymous participant")
        by_person[condition] = row

    for trials in participants.values():
        if len(trials) == 2:
            manual, toolkit = trials["manual"], trials["toolkit"]
            if manual["trial_order"] == toolkit["trial_order"]:
                raise PilotDataError("Paired trials cannot have the same trial_order")
            if (manual["os"], manual["python_version"]) != (
                toolkit["os"], toolkit["python_version"]
            ):
                raise PilotDataError("Paired trials must use the same OS and Python version")

    arms = {}
    for condition in ("manual", "toolkit"):
        subset = [r for r in rows if r["condition"] == condition]
        accepted = [r["active_minutes"] for r in subset if r["successful"]]
        arms[condition] = {
            "attempted": len(subset),
            "successful": len(accepted),
            "incomplete_or_failing": len(subset) - len(accepted),
            "completion_rate_pct": round(100 * len(accepted) / len(subset), 1) if subset else None,
            "successful_trials_median_minutes": _median(accepted),
        }

    fully_matched = [
        (v["manual"], v["toolkit"]) for v in participants.values()
        if "manual" in v and "toolkit" in v
    ]
    successful_pairs = [(a, b) for a, b in fully_matched if a["successful"] and b["successful"]]
    manual_minutes = [a["active_minutes"] for a, _ in successful_pairs]
    toolkit_minutes = [b["active_minutes"] for _, b in successful_pairs]
    manual_median = _median(manual_minutes)
    toolkit_median = _median(toolkit_minutes)
    pct = None
    if manual_median is not None and toolkit_median is not None and manual_median > 0:
        pct = round(100 * (manual_median - toolkit_median) / manual_median, 2)

    order_counts = Counter("manual_first" if a["trial_order"] == "1" else "toolkit_first"
                           for a, _ in fully_matched)
    if not rows:
        status = "no_data"
    elif len(successful_pairs) >= 5 and all(order_counts.get(k, 0) > 0
                                            for k in ("manual_first", "toolkit_first")):
        status = "pilot_data_ready_for_human_review"
    else:
        status = "exploratory_only"

    return {
        "schema_version": 1,
        "status": status,
        "study_type": "paired setup trials using common acceptance criteria",
        "participants_recorded": len(participants),
        "total_attempts": len(rows),
        "condition_summary": arms,
        "pair_summary": {
            "paired_attempts": len(fully_matched),
            "successful_comparable_pairs": len(successful_pairs),
            "unpaired_participants": len(participants) - len(fully_matched),
            "paired_but_incomplete_or_failing": len(fully_matched) - len(successful_pairs),
            "order_counts": {
                "manual_first": order_counts.get("manual_first", 0),
                "toolkit_first": order_counts.get("toolkit_first", 0),
            },
            "matched_manual_median_minutes": manual_median,
            "matched_toolkit_median_minutes": toolkit_median,
            "matched_median_difference_minutes": (
                round(manual_median - toolkit_median, 2)
                if manual_median is not None else None
            ),
            "relative_median_reduction_pct": pct,
            "median_individual_pair_difference_minutes": _median([
                a["active_minutes"] - b["active_minutes"] for a, b in successful_pairs
            ]),
        },
        "caveats": [
            "No participant-level records, identities or notes are included in this output.",
            "Only paired successful trials enter the time comparison; failures are counted separately.",
            "Small observational pilot data cannot establish causality or broad team adoption.",
            "Review trial consent, approved environment, order balance and comparable task criteria manually.",
            "CI benchmark milliseconds are not human developer minutes.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local anonymous paired-trial summary")
    parser.add_argument("--input", required=True, help="Local CSV matching M8 template")
    parser.add_argument("--json-out", help="Optional new JSON output (never overwrite)")
    args = parser.parse_args(argv)
    try:
        if args.json_out and Path(args.json_out).exists():
            raise PilotDataError("Refusing to overwrite an existing report")
        summary = analyze(args.input)
        rendered = json.dumps(summary, indent=2, allow_nan=False) + "\n"
        if args.json_out:
            with Path(args.json_out).open("x", encoding="utf-8") as handle:
                handle.write(rendered)
        print(rendered, end="")
        return 0
    except (PilotDataError, OSError) as exc:
        print(f"Pilot data validation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
