"""Exhaustive declared template/provider offline acceptance matrix.

Each supported template/provider pair is generated, Doctor-checked, checked for
safe configuration and overwrite rejection, then probed through actual ASGI
requests with AET_PROVIDER=mock. This deliberately does NOT exercise live
hosted provider inference, credentials or cost-bearing services. Generated
cloud SDK constructor tests already run in the standard generated-app suites.

Each project is unique and isolated in a temporary directory. Generated apps
share the "app" package name, so their HTTP probes run in separate interpreters.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import tempfile
from pathlib import Path

from aet_scaffolder.generator import (
    SUPPORTED_PROVIDERS,
    GenerationError,
    generate,
)
from aet_scaffolder.registry import MANIFEST_FILE, SUPPORTED_TEMPLATES, get_template
from aet_scaffolder.validator import validate_project
from scripts.release_smoke import _probe_project


_SECRET_ASSIGNMENTS = (
    "OPENAI_API_KEY=", "ANTHROPIC_API_KEY=", "AZURE_OPENAI_API_KEY=",
    "AWS_SECRET_ACCESS_KEY=", "AWS_SESSION_TOKEN=",
)


def supported_pairs() -> list[tuple[str, str]]:
    """Use the public registry, not a hardcoded subset of providers."""
    return [
        (template, provider)
        for template in SUPPORTED_TEMPLATES
        for provider in get_template(template).providers
    ]


def _must_reject(call, check: str) -> dict:
    try:
        call()
    except GenerationError:
        return {"check": check, "passed": True}
    return {"check": check, "passed": False}


def run_matrix() -> dict:
    pairs = supported_pairs()
    positive = []
    negative = []
    with tempfile.TemporaryDirectory(prefix="aet-provider-grid-") as workspace:
        root = Path(workspace)
        for template, provider in pairs:
            name = f"grid-{template}-{provider}"
            item = {
                "template": template, "provider": provider,
                "generated": False, "doctor_ok": False, "manifest_ok": False,
                "configuration_ok": False, "no_credentials_in_example": False,
                "overwrite_rejected": False, "runtime_mock_probe_ok": False,
                "corpus_change_ok": None, "passed": False,
            }
            try:
                project = generate(
                    name, output_dir=root, template=template, provider=provider,
                    model="qwen2.5:0.5b" if provider == "ollama" else None,
                )
                item["generated"] = True
                doctor = validate_project(project)
                item["doctor_ok"] = doctor.ok
                manifest = json.loads(
                    (project / MANIFEST_FILE).read_text(encoding="utf-8")
                )
                item["manifest_ok"] = (
                    manifest.get("template") == template
                    and manifest.get("schema_version") == 1
                )
                env_text = (project / ".env.example").read_text(encoding="utf-8")
                item["configuration_ok"] = (
                    f"AET_PROVIDER={provider}" in env_text.splitlines()
                    and (
                        provider != "ollama"
                        or "AET_OLLAMA_MODEL=qwen2.5:0.5b" in env_text.splitlines()
                    )
                )
                item["no_credentials_in_example"] = not any(
                    line.lstrip().startswith(_SECRET_ASSIGNMENTS)
                    for line in env_text.splitlines()
                )
                item["overwrite_rejected"] = _must_reject(
                    lambda: generate(
                        name, output_dir=root, template=template, provider=provider
                    ), "duplicate_path",
                )["passed"]
                if not all(
                    item[key] for key in (
                        "generated", "doctor_ok", "manifest_ok",
                        "configuration_ok", "no_credentials_in_example",
                        "overwrite_rejected",
                    )
                ):
                    item["failure_stage"] = "static_checks"
                else:
                    probe = _probe_project(project, template)
                    item["runtime_mock_probe_ok"] = (
                        probe["health_ok"] and probe["ready_ok"]
                        and probe["initial_api_ok"]
                        and probe["invalid_request_rejected"]
                    )
                    item["corpus_change_ok"] = probe["corpus_change_ok"]
                    item["passed"] = item["runtime_mock_probe_ok"]
            except Exception:
                # Exclude OS paths, arbitrary SDK messages and raw exceptions.
                item["failure_stage"] = (
                    "generation_or_static" if not item["generated"]
                    else "static_or_mock_api"
                )
            positive.append(item)

        for template in SUPPORTED_TEMPLATES:
            supported = get_template(template).providers
            for provider in SUPPORTED_PROVIDERS:
                if provider not in supported:
                    negative.append(_must_reject(
                        lambda t=template, p=provider: generate(
                            "unsupported-provider", output_dir=root,
                            template=t, provider=p,
                        ),
                        f"unsupported:{template}:{provider}",
                    ))
            negative.append(_must_reject(
                lambda t=template: generate(
                    "unknown-provider", output_dir=root,
                    template=t, provider="invalid-provider",
                ), f"unknown_provider:{template}",
            ))
            negative.append(_must_reject(
                lambda t=template: generate(
                    "../unsafe", output_dir=root, template=t, provider="mock",
                ), f"unsafe_name:{template}",
            ))
            for provider in supported:
                if provider != "ollama":
                    negative.append(_must_reject(
                        lambda t=template, p=provider: generate(
                            "bad-cloud-model", output_dir=root, template=t,
                            provider=p, model="fake-model",
                        ), f"unexpected_model_arg:{template}:{provider}",
                    ))

    all_passed = (
        len(pairs) == len(positive)
        and all(item["passed"] for item in positive)
        and all(item["passed"] for item in negative)
    )
    report = {
        "schema_version": 1,
        "evidence_type": "declared_template_provider_offline_matrix",
        "environment": {
            "os": platform.system(),
            "python": f"{sys.version_info.major}.{sys.version_info.minor}",
        },
        "status": "pass" if all_passed else "fail",
        "pair_count": len(pairs),
        "passed_pairs": sum(item["passed"] for item in positive),
        "negative_check_count": len(negative),
        "passed_negative_checks": sum(item["passed"] for item in negative),
        "scope": (
            "generation, manifest, environment example, Doctor, anti-overwrite, "
            "actual FastAPI TestClient requests in a fresh subprocess forced to "
            "offline mock, RAG corpus mutation, invalid inputs and negative flags"
        ),
        "limitations": {
            "cloud_live_inference_verified": False,
            "ollama_real_daemon_verified": False,
            "cloud_sdk_doubles_tested_separately": True,
            "installation_repeated_for_each_pair": False,
            "production_security_verified": False,
            "human_adoption_or_time_saved_verified": False,
        },
        "pairs": positive,
        "negative_checks": negative,
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run all declared AET pairs using isolated offline probes"
    )
    parser.add_argument("--json-out", required=True, metavar="NEW_JSON_PATH")
    args = parser.parse_args(argv)
    destination = Path(args.json_out)
    if destination.exists():
        parser.error("refusing to overwrite an existing report")
    report = run_matrix()
    try:
        with destination.open("x", encoding="utf-8") as file:
            json.dump(report, file, indent=2)
            file.write("\n")
    except OSError:
        print("Unable to create offline evidence report.", file=sys.stderr)
        return 2
    print(json.dumps({
        key: report[key] for key in (
            "evidence_type", "environment", "status", "pair_count",
            "passed_pairs", "negative_check_count", "passed_negative_checks"
        )
    }))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
