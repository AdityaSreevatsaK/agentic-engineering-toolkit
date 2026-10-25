"""Run a temporary, local-only demo across all three AET assets.

Never installs packages, starts a listener, downloads models or contacts cloud APIs.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from aet_scaffolder.generator import generate
from aet_scaffolder.validator import validate_project


_REQUIRED = ("aet_quality", "aet_provider", "fastapi", "langgraph", "httpx", "pydantic_settings")


def demo() -> dict:
    """Generate and validate an app, then verify its API in a separate interpreter."""
    missing = [name for name in _REQUIRED if importlib.util.find_spec(name) is None]
    if missing:
        raise RuntimeError(
            "Missing demo dependencies: " + ", ".join(missing)
            + ". Install the three packages and the demo extras as documented in docs/demo/README.md"
        )

    probe = Path(__file__).with_name("_demo_probe.py").resolve()
    if not probe.is_file():
        raise RuntimeError("Demo probe script is missing")
    with tempfile.TemporaryDirectory(prefix="aet-e2e-demo-") as temp:
        project = generate("demo-agent", output_dir=temp, provider="mock")
        static = validate_project(project)
        if not static.ok:
            names = [check.name for check in static.checks if not check.passed]
            raise RuntimeError("Generated project static validation failed: " + ", ".join(names))

        environment = os.environ.copy()
        # The demo is always offline/mocked, even when the user's shell has
        # production or local-model settings configured.
        environment["AET_PROVIDER"] = "mock"
        environment["AET_OLLAMA_MODEL"] = "llama3.2:1b"
        environment["AET_OLLAMA_BASE_URL"] = "http://127.0.0.1:11434"
        environment["AET_OLLAMA_TIMEOUT_SECONDS"] = "90"
        environment["PYTHONPATH"] = str(project)

        completed = subprocess.run(
            [sys.executable, str(probe)],
            cwd=str(project),
            env=environment,
            text=True,
            capture_output=True,
            timeout=90,
            check=False,
        )
        if completed.returncode:
            # Never reveal captured subprocess output in CLI errors: its
            # environment may contain sensitive developer-local settings.
            raise RuntimeError(f"Generated-agent probe failed with exit code {completed.returncode}")
        try:
            result = json.loads(completed.stdout)
        except ValueError as exc:
            raise RuntimeError("Generated-agent probe produced invalid JSON") from exc
        if result.get("status") != "passed" or not isinstance(result.get("checks"), list):
            raise RuntimeError("Generated-agent probe did not report successful checks")
        return {
            "schema_version": 1,
            "status": "passed",
            "scenario": "fully local deterministic end-to-end demo",
            "project_validation": {"status": "passed", "checks": len(static.checks)},
            "integration": result,
            "scope": (
                "Synthetic data; mock providers and injected fake Ollama transport only. "
                "No network service, live language model, developer productivity or cloud compatibility measured."
            ),
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the three AET assets together, offline")
    parser.add_argument("--json-out", help="Save a sanitized result to a new JSON file; no overwrite")
    args = parser.parse_args(argv)
    if args.json_out and Path(args.json_out).exists():
        print("Demo result file already exists; refusing overwrite", file=sys.stderr)
        return 2
    try:
        result = demo()
        output = json.dumps(result, indent=2) + "\n"
        if args.json_out:
            with Path(args.json_out).open("x", encoding="utf-8") as handle:
                handle.write(output)
        print(output, end="")
        return 0
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"Demo check failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
