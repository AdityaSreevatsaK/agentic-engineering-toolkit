"""Fresh virtualenv installation and mock API probe of all four generated apps.

Avoid cross-project import bleed: generated projects all define package 'app'.
Requires PyPI dependency resolution, but never invokes a paid model provider.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import tempfile
import venv
from pathlib import Path

from aet_scaffolder.generator import generate
from aet_scaffolder.registry import SUPPORTED_TEMPLATES
from scripts.release_smoke import _PROBE, _clean_environment


def _run(arguments: list[str], *, cwd: Path, stage: str, timeout: int = 420,
         env: dict[str, str] | None = None) -> str:
    result = subprocess.run(arguments, cwd=cwd, env=env, text=True, capture_output=True,
                            timeout=timeout, check=False)
    if result.returncode:
        # Do not attach arbitrary pip or application logs to public evidence.
        raise RuntimeError(f"{stage} failed (exit status {result.returncode})")
    return result.stdout


def verify_isolated_installations(versions_dir: Path) -> list[dict]:
    if versions_dir.exists():
        raise ValueError("Refusing to overwrite an existing dependency report directory")
    versions_dir.mkdir(parents=True)
    results = []
    with tempfile.TemporaryDirectory(prefix="aet-isolated-") as root:
        for template in SUPPORTED_TEMPLATES:
            project = generate(f"isolated-{template}", output_dir=root, template=template)
            environment = Path(root) / f"venv-{template}"
            venv.EnvBuilder(with_pip=True).create(environment)
            interpreter = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            _run([str(interpreter), "-m", "pip", "install", "-e", ".[dev]"], cwd=project,
                 stage=f"{template}/install", timeout=600)
            _run([str(interpreter), "-m", "pip", "check"], cwd=project,
                 stage=f"{template}/pip-check")
            output = _run([str(interpreter), "-m", "pytest", "-q"], cwd=project,
                          env=_clean_environment(), stage=f"{template}/pytest")
            match = re.search(r"(\d+) passed", output)
            if not match:
                raise RuntimeError(f"{template}/pytest summary not recognised")
            _run([str(interpreter), "-c", _PROBE, template], cwd=project,
                 env=_clean_environment(), stage=f"{template}/api")
            versions = _run([str(interpreter), "-m", "pip", "freeze", "--all"], cwd=project,
                            stage=f"{template}/versions")
            (versions_dir / f"{template}.txt").write_text(versions, encoding="utf-8")
            results.append({"template": template, "provider": "mock",
                            "python": platform.python_version(), "venv_isolated": True,
                            "package_installed": True, "pip_check": True,
                            "generated_app_tests_passed": int(match.group(1)),
                            "actual_asgi_probe": True})
            print(f"PASS isolated install: {template}", flush=True)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--versions-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.json_out.exists():
        parser.error("Refusing to overwrite existing evidence")
    results = verify_isolated_installations(args.versions_dir)
    args.json_out.write_text(json.dumps({"scope": "fresh isolated venv and local ASGI mock only",
                                         "results": results}, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
