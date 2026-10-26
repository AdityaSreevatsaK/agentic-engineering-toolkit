"""Local AET M15 structural adoption preflight.

This script is automated evidence only. It never measures human setup time,
checks live provider quality, verifies team adoption or contacts external APIs.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from aet_scaffolder.generator import generate
from aet_scaffolder.registry import MANIFEST_FILE, TEMPLATES
from aet_scaffolder.validator import validate_project


def run_preflight() -> dict:
    """Generate each offline template in a disposable directory and run Doctor."""
    results: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="aet-m15-") as temp:
        for template in TEMPLATES:
            result: dict = {
                "template": template,
                "generated": False,
                "doctor_ok": False,
                "manifest_ok": False,
                "offline_default": False,
                "legal_files_present": False,
                "generated_ci_present": False,
                "passed": False,
            }
            try:
                target = generate(
                    f"pilot-{template}", output_dir=temp,
                    template=template, provider="mock",
                )
                result["generated"] = True
                report = validate_project(target)
                result["doctor_ok"] = bool(report.ok)
                manifest = json.loads((target / MANIFEST_FILE).read_text(encoding="utf-8"))
                result["manifest_ok"] = (
                    manifest.get("template") == template
                    and manifest.get("schema_version") == 1
                )
                result["offline_default"] = (
                    "AET_PROVIDER=mock" in
                    (target / ".env.example").read_text(encoding="utf-8")
                )
                result["legal_files_present"] = all(
                    (target / name).is_file() for name in ("LICENSE", "NOTICE")
                )
                result["generated_ci_present"] = (
                    target / ".github" / "workflows" / "ci.yml"
                ).is_file()
                result["passed"] = all(
                    result[key] for key in (
                        "generated", "doctor_ok", "manifest_ok",
                        "offline_default", "legal_files_present", "generated_ci_present",
                    )
                )
            except (OSError, ValueError, KeyError, TypeError) as exc:
                # Exception *type* is enough; never print paths or source content.
                result["error_type"] = type(exc).__name__
            results.append(result)
    return {
        "schema_version": 1,
        "evidence_type": "automated_structural_preflight",
        "independent_human_trial": False,
        "human_time_saved": None,
        "live_provider_verified": False,
        "status": "pass" if results and all(r["passed"] for r in results) else "fail",
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Local, non-human structural adoption preflight. No cloud calls."
    )
    parser.add_argument(
        "--json-out", metavar="NEW_PATH",
        help="Write a new machine-only JSON report; refuses to overwrite",
    )
    args = parser.parse_args(argv)
    report = run_preflight()
    if args.json_out:
        try:
            with Path(args.json_out).open("x", encoding="utf-8") as file:
                json.dump(report, file, indent=2)
                file.write("\n")
        except OSError as exc:
            print(
                f"Could not create report ({type(exc).__name__}); existing files are not overwritten.",
                file=sys.stderr,
            )
            return 2
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
