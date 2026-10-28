"""M19 isolated-workspace, offline generated-app acceptance smoke.

This uses the currently installed scaffolder and installed generated-app
dependencies. It is NOT a fresh-user trial, install benchmark, security
assessment or evidence of developer time saved. No external HTTP service is
started; FastAPI TestClient exercises actual ASGI requests in a child process.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from time import perf_counter

from aet_scaffolder.generator import generate
from aet_scaffolder.registry import SUPPORTED_TEMPLATES
from aet_scaffolder.validator import validate_project


# Execute generated apps in separate interpreters so their shared "app"
# package name cannot contaminate other templates via sys.modules.
# Only fixed, synthetic inputs are sent; no provider SDK is called.
_PROBE = r"""
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from app.main import app

template = sys.argv[1]
is_rag = template in {"langgraph-rag", "llamaindex-rag"}
with TestClient(app) as client:
    assert client.get("/health").status_code == 200
    ready = client.get("/ready")
    assert ready.status_code == 200, "offline readiness failed"
    if is_rag:
        response = client.post("/ask", json={
            "question": "What is the sample return policy?"
        })
        assert response.status_code == 200, "original knowledge request failed"
        original = response.json()
        assert "returns" in original["source_ids"], "return source missing"
        assert "30 days" in original["answer"], "return policy absent"

        # Only the temporary generated project's corpus is changed.
        path = Path("data/knowledge.jsonl")
        with path.open("a", encoding="utf-8") as file:
            file.write("\n" + json.dumps({
                "id": "violet-manual",
                "text": "Violet reference manuals are indexed on Thursday."
            }) + "\n")
        changed = client.post("/ask", json={
            "question": "Which day are violet reference manuals indexed?"
        })
        assert changed.status_code == 200, "amended knowledge request failed"
        changed_result = changed.json()
        assert "violet-manual" in changed_result["source_ids"], "amended source missing"
        assert "Thursday" in changed_result["answer"], "changed evidence absent"
    else:
        response = client.post("/invoke", json={
            "question": "order status ORD-1001"
        })
        assert response.status_code == 200, "synthetic order request failed"
        result = response.json()
        assert "shipped" in result["answer"].lower(), "synthetic order status absent"
        assert result["tool_used"], "synthetic tool invocation absent"
    invalid = client.post("/ask" if is_rag else "/invoke", json={"question": ""})
    assert invalid.status_code == 422, "invalid input was accepted"

print("AET_M19_PROBE=" + json.dumps({
    "health_ok": True,
    "ready_ok": True,
    "initial_api_ok": True,
    "corpus_change_ok": True if is_rag else None,
    "invalid_request_rejected": True
}, separators=(",", ":")))
"""


def _clean_environment() -> dict[str, str]:
    """Pass only Python/OS runtime settings, never host cloud credentials."""
    allowed = {
        "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP",
        "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "VIRTUAL_ENV",
        "LANG", "LC_ALL", "PYTHONUTF8", "PYTHONIOENCODING",
    }
    child = {key: value for key, value in os.environ.items()
             if key.upper() in allowed}
    child["AET_PROVIDER"] = "mock"
    child["AET_KNOWLEDGE_PATH"] = "data/knowledge.jsonl"
    child["PYTHONNOUSERSITE"] = "1"
    child["PYTHONDONTWRITEBYTECODE"] = "1"
    return child


def _probe_project(project: Path, template: str) -> dict:
    """Actual ASGI HTTP + synthetic corpus mutation in a child interpreter."""
    try:
        proc = subprocess.run(
            [sys.executable, "-c", _PROBE, template],
            cwd=project,
            env=_clean_environment(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("api_probe_timeout") from exc
    if proc.returncode != 0:
        # Never copy stdout/stderr, exception text, paths or prompts to reports.
        raise RuntimeError("api_probe_failed")
    matches = [
        line.removeprefix("AET_M19_PROBE=")
        for line in proc.stdout.splitlines()
        if line.startswith("AET_M19_PROBE=")
    ]
    if len(matches) != 1:
        raise RuntimeError("api_probe_output_invalid")
    try:
        response = json.loads(matches[0])
    except ValueError as exc:
        raise RuntimeError("api_probe_output_invalid") from exc
    if (
        response.get("health_ok") is not True
        or response.get("ready_ok") is not True
        or response.get("initial_api_ok") is not True
        or response.get("invalid_request_rejected") is not True
        or (template in {"langgraph-rag", "llamaindex-rag"}
            and response.get("corpus_change_ok") is not True)
    ):
        raise RuntimeError("api_probe_checks_failed")
    return response


def run_release_smoke() -> dict:
    """Produce structural+HTTP machine evidence, without any human claims."""
    results = []
    with tempfile.TemporaryDirectory(prefix="aet-m19-smoke-") as temp:
        for template in SUPPORTED_TEMPLATES:
            item: dict = {
                "template": template,
                "provider": "mock",
                "generated": False,
                "doctor_ok": False,
                "health_ok": False,
                "ready_ok": False,
                "initial_api_ok": False,
                "corpus_change_ok": None,
                "invalid_request_rejected": False,
                "passed": False,
            }
            started = perf_counter()
            try:
                project = generate(
                    f"m19-{template}", template=template, provider="mock",
                    output_dir=temp,
                )
                item["generated"] = True
                generated_at = perf_counter()
                report = validate_project(project)
                item["doctor_ok"] = bool(report.ok)
                if not item["doctor_ok"]:
                    raise RuntimeError("doctor_failed")
                doctor_at = perf_counter()
                checks = _probe_project(project, template)
                item.update(checks)
                probe_at = perf_counter()
                item["passed"] = True
                item["generation_ms"] = round((generated_at - started) * 1000, 2)
                item["doctor_ms"] = round((doctor_at - generated_at) * 1000, 2)
                item["api_probe_ms"] = round((probe_at - doctor_at) * 1000, 2)
            except Exception as exc:
                # Errors are deliberately a closed vocabulary; never expose
                # arbitrary exception content, local paths or host details.
                item["failure_stage"] = (
                    "generation" if not item["generated"]
                    else "doctor" if not item["doctor_ok"]
                    else "api_probe"
                )
                item["passed"] = False
            results.append(item)
    return {
        "schema_version": 1,
        "evidence_type": "automated_local_application_smoke",
        "environment": {
            "os": platform.system(),
            "python": f"{sys.version_info.major}.{sys.version_info.minor}",
        },
        "status": "pass" if results and all(x["passed"] for x in results) else "fail",
        "independent_human_trial": False,
        "multi_team_adoption_verified": False,
        "human_time_saved": None,
        "live_provider_verified": False,
        "machine_timing_scope": (
            "generated files, static Doctor, child-process ASGI probes only; "
            "excludes dependency installation and human work"
        ),
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run temporary offline generated-app HTTP smoke; no human adoption claims."
    )
    parser.add_argument(
        "--json-out", metavar="NEW_PATH",
        help="Write a new, sanitised machine-only JSON report; refuses overwrites",
    )
    args = parser.parse_args(argv)
    if args.json_out and Path(args.json_out).exists():
        print("Refusing to overwrite existing report.", file=sys.stderr)
        return 2
    report = run_release_smoke()
    if args.json_out:
        try:
            with Path(args.json_out).open("x", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
                f.write("\n")
        except OSError:
            print("Could not write new machine-only report.", file=sys.stderr)
            return 2
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
