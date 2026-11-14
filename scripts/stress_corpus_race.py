"""Repeat a real generated RAG app's bounded atomic-corpus event on Windows.

Uses the existing credential-stripped mock ASGI child. Each trial generates a
fresh application with a distinct path. No paid provider, network listener,
customer content or persistent local corpus is involved.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import tempfile
from pathlib import Path

from aet_scaffolder.generator import generate
from aet_scaffolder.validator import validate_project
from scripts.deep_event_matrix import run_pair

TEMPLATE = "langgraph-rag"
PROVIDER = "openai"
SCENARIO = "concurrent_atomic_corpus_updates"


def run_trials(trials: int, *, templates: tuple[str, ...] = (TEMPLATE,)) -> dict:
    if not 1 <= trials <= 20:
        raise ValueError("trials must be between 1 and 20")
    if not templates or len(set(templates)) != len(templates) or any(
        item not in (TEMPLATE, "llamaindex-rag") for item in templates
    ):
        raise ValueError("invalid or duplicate RAG template")
    outcomes: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="aet-corpus-race-") as temporary:
        for template in templates:
            for attempt in range(1, trials + 1):
                project = generate(
                    f"corpus-race-{template}-{attempt}", output_dir=temporary,
                    template=template, provider=PROVIDER,
                )
                if not validate_project(project).ok:
                    outcome = {"template": template, "trial": attempt, "passed": False,
                               "failure_stage": "doctor_failed"}
                else:
                    result = run_pair(template, PROVIDER, project)
                    matching = [
                        e for e in result.get("events", []) if e.get("scenario") == SCENARIO
                    ]
                    if len(matching) != 1:
                        outcome = {"template": template, "trial": attempt, "passed": False,
                                   "failure_stage": result.get("failure_stage",
                                                               "missing_scenario")}
                    else:
                        event = matching[0]
                        # Explicit fields only: no raw failures, prompts or response bodies.
                        outcome = {
                            "template": template,
                            "trial": attempt,
                            "passed": result.get("passed") is True
                                      and event.get("passed") is True,
                            "race_passed": event.get("passed") is True,
                            "writer_completed": event.get("writer_completed") is True,
                            "atomic_replace_failed":
                                event.get("atomic_replace_failed") is True,
                            "non_200_response_count": min(
                                12, max(0, int(event.get("non_200_response_count", 0)))
                            ),
                            "non_200_http_statuses": sorted({
                                status for status in event.get("non_200_http_statuses", [])
                                if type(status) is int and 400 <= status <= 599
                            })[:12],
                        }
                outcomes.append(outcome)
                print(
                    f"{'PASS' if outcome['passed'] else 'FAIL'} corpus race "
                    f"{template} trial {attempt}/{trials}",
                    flush=True,
                )
    return {
        "schema_version": 1,
        "evidence_type": "bounded_windows_corpus_race_repetition",
        "environment": {"os": platform.system(),
                        "python": f"{sys.version_info.major}.{sys.version_info.minor}"},
        "scope": "synthetic local mock ASGI and bounded atomic corpus replacements",
        "template": templates[0] if len(templates) == 1 else "both",
        "templates": list(templates),
        "configured_provider": PROVIDER,
        "live_provider_called": False,
        "rounds_per_template": trials,
        "trial_count": len(outcomes),
        "passed_trials": sum(item["passed"] for item in outcomes),
        "status": "pass" if all(item["passed"] for item in outcomes) else "fail",
        "trials": outcomes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=8)
    parser.add_argument("--template", choices=(TEMPLATE, "llamaindex-rag", "both"),
                        default=TEMPLATE)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args(argv)
    if not 1 <= args.trials <= 20:
        parser.error("--trials must be between 1 and 20")
    templates = (TEMPLATE, "llamaindex-rag") if args.template == "both" else (args.template,)
    report = run_trials(args.trials, templates=templates)
    try:
        with args.json_out.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(report, handle, indent=2)
            handle.write("\n")
    except FileExistsError:
        parser.error("refusing to overwrite existing evidence")
    print(json.dumps({"status": report["status"], "trial_count": report["trial_count"],
                      "passed_trials": report["passed_trials"]}))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
