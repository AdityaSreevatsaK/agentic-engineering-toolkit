"""SHA-256 evidence inventory must be deterministic, bounded and non-secret."""
import hashlib
import json

import pytest

from scripts import evidence_manifest


def test_manifest_contains_only_base_names_commits_and_digests(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    monkeypatch.setenv("GITHUB_RUN_ID", "12345")
    file = tmp_path / "metrics.csv"
    file.write_bytes(b"safe,synthetic\n")
    manifest = evidence_manifest.manifest_for([file])
    assert manifest["cryptographically_signed"] is False
    assert manifest["source_commit"] == "a" * 40
    assert manifest["workflow_run_id"] == "12345"
    assert manifest["artifacts"] == [{
        "filename": "metrics.csv",
        "size_bytes": len(b"safe,synthetic\n"),
        "sha256": hashlib.sha256(b"safe,synthetic\n").hexdigest(),
    }]
    assert str(tmp_path) not in json.dumps(manifest)


def test_disallows_duplicate_basename_and_symlinks(tmp_path):
    a = tmp_path / "one"
    b = tmp_path / "two"
    a.mkdir()
    b.mkdir()
    (a / "results.json").write_text("{}")
    (b / "results.json").write_text("{}")
    with pytest.raises(ValueError, match="distinct"):
        evidence_manifest.manifest_for(
            [a / "results.json", b / "results.json"]
        )
    link = tmp_path / "link.json"
    try:
        link.symlink_to(a / "results.json")
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks are not available on this platform")
    with pytest.raises(ValueError):
        evidence_manifest.digest(link)


def test_cli_writes_and_refuses_to_overwrite(tmp_path):
    source = tmp_path / "sample.csv"
    source.write_text("hello", encoding="utf-8")
    dest = tmp_path / "manifest.json"
    assert evidence_manifest.main([
        "--out", str(dest), str(source)
    ]) == 0
    assert json.loads(dest.read_text())["artifacts"][0]["filename"] == "sample.csv"
    with pytest.raises(SystemExit):
        evidence_manifest.main(["--out", str(dest), str(source)])
