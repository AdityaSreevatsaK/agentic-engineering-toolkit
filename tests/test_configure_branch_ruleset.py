"""Offline tests for GitHub owner-operated branch protection helper."""
import json

from scripts import configure_branch_ruleset as ruleset


def test_payload_protects_master_and_all_five_checks():
    payload = ruleset.desired_ruleset()
    assert payload["enforcement"] == "active"
    assert payload["bypass_actors"] == []
    assert payload["conditions"]["ref_name"]["include"] == ["~DEFAULT_BRANCH"]
    assert ruleset._verified(payload)
    params = next(
        x["parameters"] for x in payload["rules"]
        if x["type"] == "pull_request"
    )
    assert params["required_approving_review_count"] == 0
    assert params["required_review_thread_resolution"] is True


def test_missing_check_or_inactive_ruleset_fails_verification():
    payload = ruleset.desired_ruleset()
    payload["enforcement"] = "disabled"
    assert not ruleset._verified(payload)
    payload["enforcement"] = "active"
    checks = next(
        x["parameters"] for x in payload["rules"]
        if x["type"] == "required_status_checks"
    )
    checks["required_status_checks"].pop()
    assert not ruleset._verified(payload)


def test_plan_does_not_contact_github(monkeypatch, capsys):
    monkeypatch.setattr(ruleset, "_api", lambda *a, **k: 1 / 0)
    assert ruleset.main([]) == 0
    output = capsys.readouterr().out
    assert "PLAN ONLY" in output
    assert json.loads(output.split("\nPLAN ONLY:", 1)[0])["target"] == "branch"


def test_apply_and_verify_with_stubbed_gh(monkeypatch, capsys):
    requests = []
    full = dict(ruleset.desired_ruleset(), id=8127)

    def fake_api(path, *, method="GET", payload=None):
        requests.append((path, method))
        if method == "POST":
            assert payload == ruleset.desired_ruleset()
            return full
        if path.endswith("/8127"):
            return full
        if len(requests) == 1:
            return []
        return [{"id": 8127, "name": ruleset.RULESET_NAME}]

    monkeypatch.setattr(ruleset, "_api", fake_api)
    assert ruleset.main(["--apply"]) == 0
    assert ("repos/" + ruleset.REPOSITORY + "/rulesets", "POST") in requests
    requests.clear()
    assert ruleset.main(["--verify"]) == 0
    assert all(method == "GET" for _, method in requests)


def test_apply_is_idempotent_and_does_not_rewrite_existing(monkeypatch):
    requests = []
    payload = dict(ruleset.desired_ruleset(), id=2)

    def fake_api(path, *, method="GET", payload=None):
        requests.append(method)
        if path.endswith("/2"):
            return configured
        return [{"id": 2, "name": ruleset.RULESET_NAME}]

    configured = payload
    monkeypatch.setattr(ruleset, "_api", fake_api)
    assert ruleset.main(["--apply"]) == 0
    assert requests == ["GET", "GET"]


def test_verify_fails_when_not_configured(monkeypatch, capsys):
    monkeypatch.setattr(ruleset, "_api", lambda *a, **k: [])
    assert ruleset.main(["--verify"]) == 1
    assert "not configured" in capsys.readouterr().err
