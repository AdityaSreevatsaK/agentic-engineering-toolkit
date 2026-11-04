"""Owner-operated, idempotent GitHub branch ruleset setup for AET.

No tokens, credentials, or access grants are handled here: GitHub CLI handles
the existing user's authentication. Read-only --plan is the default. --apply
requires an explicit local command with admin-scoped GitHub CLI credentials.
This script never removes, weakens or overwrites an existing ruleset.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any

REPOSITORY = "AdityaSreevatsaK/agentic-engineering-toolkit"
RULESET_NAME = "Protect master: PR and five CI checks"
CHECKS = (
    "smoke (ubuntu-24.04, 3.11)",
    "smoke (ubuntu-24.04, 3.12)",
    "smoke (windows-2025, 3.11)",
    "smoke (windows-2025, 3.12)",
    "quality (ruff, mypy, bandit)",
)
ENDPOINT = f"repos/{REPOSITORY}/rulesets"


class RulesetError(RuntimeError):
    """A non-sensitive configuration/permission issue to show to the owner."""


def desired_ruleset() -> dict[str, Any]:
    """Generate the GitHub repository-ruleset REST API payload."""
    return {
        "name": RULESET_NAME,
        "target": "branch",
        "enforcement": "active",
        "bypass_actors": [],
        "conditions": {
            "ref_name": {
                "include": ["~DEFAULT_BRANCH"],
                "exclude": [],
            }
        },
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {
                "type": "pull_request",
                "parameters": {
                    "required_approving_review_count": 0,
                    "dismiss_stale_reviews_on_push": True,
                    "require_code_owner_review": False,
                    "require_last_push_approval": False,
                    "required_review_thread_resolution": True,
                    "allowed_merge_methods": ["merge", "squash", "rebase"],
                },
            },
            {
                "type": "required_status_checks",
                "parameters": {
                    "strict_required_status_checks_policy": True,
                    "required_status_checks": [
                        {"context": name} for name in CHECKS
                    ],
                },
            },
        ],
    }


def _api(path: str, *, method: str = "GET",
         payload: dict[str, Any] | None = None) -> Any:
    command = [
        "gh", "api", path, "--method", method,
        "--header", "Accept: application/vnd.github+json",
    ]
    if payload is not None:
        command.extend(("--input", "-"))
    try:
        completed = subprocess.run(
            command,
            input=json.dumps(payload) if payload is not None else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=35,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RulesetError(
            "GitHub CLI (gh) is not installed. Install it and run 'gh auth login'."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise RulesetError(
            "GitHub CLI request timed out; inspect rulesets before retrying."
        ) from exc
    if completed.returncode != 0:
        # Never print potentially sensitive stderr or credential data.
        raise RulesetError(
            "GitHub API request failed. Verify 'gh auth status', repository "
            "administration permission and GitHub ruleset support."
        )
    try:
        return json.loads(completed.stdout)
    except ValueError as exc:
        raise RulesetError("GitHub API returned an unexpected response.") from exc


def _matching_ruleset() -> dict[str, Any] | None:
    rulesets = _api(ENDPOINT)
    if not isinstance(rulesets, list):
        raise RulesetError("Could not inspect the repository's rulesets.")
    matches = [
        item for item in rulesets
        if isinstance(item, dict) and item.get("name") == RULESET_NAME
    ]
    if len(matches) > 1:
        raise RulesetError("Multiple similarly named rulesets exist; review manually.")
    return matches[0] if matches else None


def _verified(payload: dict[str, Any]) -> bool:
    """Verify actual repository rules, not merely that POST succeeded."""
    if (
        payload.get("name") != RULESET_NAME
        or payload.get("target") != "branch"
        or payload.get("enforcement") != "active"
        or "~DEFAULT_BRANCH" not in payload.get("conditions", {})
            .get("ref_name", {}).get("include", [])
    ):
        return False
    rules = {
        rule["type"]: rule for rule in payload.get("rules", [])
        if isinstance(rule, dict) and isinstance(rule.get("type"), str)
    }
    if not {"pull_request", "required_status_checks",
            "deletion", "non_fast_forward"} <= rules.keys():
        return False
    pr = rules["pull_request"].get("parameters", {})
    if (
        pr.get("required_approving_review_count") != 0
        or pr.get("required_review_thread_resolution") is not True
    ):
        return False
    check_parameters = rules["required_status_checks"].get("parameters", {})
    contexts = {
        item.get("context")
        for item in check_parameters.get("required_status_checks", [])
        if isinstance(item, dict)
    }
    return (
        check_parameters.get("strict_required_status_checks_policy") is True
        and contexts == set(CHECKS)
    )


def _read_ruleset(info: dict[str, Any]) -> dict[str, Any]:
    ruleset_id = info.get("id")
    if not isinstance(ruleset_id, int):
        raise RulesetError("GitHub did not return a ruleset ID.")
    details = _api(f"{ENDPOINT}/{ruleset_id}")
    if not isinstance(details, dict):
        raise RulesetError("Could not verify ruleset details.")
    return details


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Plan, apply or verify AET master protection via your local gh login"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true",
                       help="Create an active ruleset using your gh login")
    group.add_argument("--verify", action="store_true",
                       help="Read GitHub ruleset status without making changes")
    args = parser.parse_args(argv)

    if not args.apply and not args.verify:
        print(json.dumps(desired_ruleset(), indent=2))
        print("PLAN ONLY: no GitHub API call or settings change was made.")
        return 0
    try:
        existing = _matching_ruleset()
        if args.verify:
            if existing is None:
                raise RulesetError("Branch protection is not configured.")
            if not _verified(_read_ruleset(existing)):
                raise RulesetError("Existing branch ruleset is incomplete or inactive.")
            print("VERIFIED: active master ruleset enforces PRs and all five checks.")
            return 0

        if existing is None:
            created = _api(ENDPOINT, method="POST", payload=desired_ruleset())
            if not isinstance(created, dict):
                raise RulesetError("Unexpected create response; inspect GitHub rulesets.")
            existing = created
        # Do not modify or weaken a pre-existing ruleset, even if incomplete.
        if not _verified(_read_ruleset(existing)):
            raise RulesetError(
                "Ruleset exists but verification failed. Review GitHub Settings "
                "rather than rerunning a write or modifying an existing ruleset."
            )
        print("VERIFIED: active master ruleset enforces PRs and all five checks.")
        return 0
    except RulesetError as exc:
        print(f"Ruleset setup/verification: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
