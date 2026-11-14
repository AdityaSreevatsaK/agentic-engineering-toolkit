"""Build and locally HTTP-probe all four generated development Docker images.

Only synthetic mock requests are used. All ports bind to 127.0.0.1.
Never expose these unauthenticated starter applications externally.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from uuid import uuid4

_PROJECTS = (
    ("tool-agent", "mock-demo", "/invoke", "order status ORD-1001"),
    ("langgraph-rag", "rag-demo", "/ask", "What is the return policy?"),
    ("strands-agent", "strands-demo", "/invoke", "order status ORD-1001"),
    ("llamaindex-rag", "llamaindex-demo", "/ask", "What is the return policy?"),
)


def _docker(*args: str, timeout: int = 120) -> str:
    process = subprocess.run(
        ["docker", *args], capture_output=True, text=True, check=False,
        timeout=timeout,
    )
    if process.returncode:
        # Do not copy arbitrary process logs or environment values to evidence.
        raise RuntimeError(f"docker {args[0]} failed with exit code {process.returncode}")
    return process.stdout.strip()


def _request(url: str, *, question: str | None = None) -> tuple[int, dict]:
    data = None if question is None else json.dumps({"question": question}).encode("utf-8")
    request = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"} if data else {},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, {}


def _check_container(name: str, endpoint: str, question: str) -> None:
    binding = _docker("port", name, "8000/tcp")
    match = re.fullmatch(r"127\.0\.0\.1:(\d+)", binding)
    if not match:
        raise RuntimeError("Container is not bound exclusively to 127.0.0.1")
    base = f"http://127.0.0.1:{int(match.group(1))}"
    deadline = time.monotonic() + 90
    while True:
        try:
            status, health = _request(base + "/health")
            if status == 200 and health.get("status") == "ok":
                break
        except (OSError, TimeoutError):
            pass
        if time.monotonic() >= deadline:
            raise RuntimeError("Container HTTP health probe timed out")
        time.sleep(0.5)

    status, ready = _request(base + "/ready")
    if status != 200 or ready.get("status") != "ready":
        raise RuntimeError("Container readiness probe failed")
    status, result = _request(base + endpoint, question=question)
    if status != 200 or not isinstance(result.get("answer"), str) or not result["answer"]:
        raise RuntimeError("Container synthetic API probe failed")
    status, _ = _request(base + endpoint, question="")
    if status != 422:
        raise RuntimeError("Container invalid request was not rejected")


def run_docker_smoke(root: Path) -> list[dict[str, str | bool]]:
    """Build, run, probe and remove each reference container in sequence."""
    results = []
    for template, path, endpoint, question in _PROJECTS:
        project = root / path
        if not project.is_dir():
            raise RuntimeError(f"Missing generated project for {template}")
        tag = f"aet-docker-smoke-{template}"
        _docker("build", "--quiet", "--tag", tag, str(project), timeout=420)
        container = f"aet-smoke-{uuid4().hex[:12]}"
        try:
            _docker(
                "run", "--detach", "--rm", "--name", container,
                "--publish", "127.0.0.1::8000", tag,
            )
            _check_container(container, endpoint, question)
            results.append({"template": template, "built": True, "health": True,
                            "ready": True, "synthetic_api": True, "invalid_input": True})
            print(f"PASS docker smoke: {template}", flush=True)
        finally:
            subprocess.run(["docker", "rm", "--force", container],
                           capture_output=True, timeout=20, check=False)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, required=True)
    options = parser.parse_args()
    if options.json_out.exists():
        parser.error("refusing to replace existing evidence")
    results = run_docker_smoke(Path.cwd())
    options.json_out.write_text(json.dumps({"scope": "local-only Docker mock HTTP smoke",
                                            "results": results}, indent=2) + "\n",
                                encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
