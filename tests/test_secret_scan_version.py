"""Keep the GitHub action and TruffleHog scanner image versions in sync."""

import re
from pathlib import Path


def test_trufflehog_action_and_scanner_versions_match() -> None:
    workflow = (
        Path(__file__).resolve().parents[1] / ".github" / "workflows" / "secret-scan.yml"
    ).read_text(encoding="utf-8")
    action = re.search(
        r"(?m)^\\s*uses:\\s*trufflesecurity/trufflehog@[a-f0-9]{40}\\s*#\\s*v(?P<version>[0-9]+\\.[0-9]+\\.[0-9]+)\\s*$",
        workflow,
    )
    scanner = re.search(
        r"(?m)^\\s*version:\\s*['\\\"]?(?P<version>[0-9]+\\.[0-9]+\\.[0-9]+)['\\\"]?\\s*$",
        workflow,
    )
    assert action is not None, "TruffleHog action must be SHA-pinned with a version comment"
    assert scanner is not None, "TruffleHog scanner image version must be explicit"
    assert action.group("version") == scanner.group("version"), (
        "TruffleHog action and scanner versions have drifted"
    )
