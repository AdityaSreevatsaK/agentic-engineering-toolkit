"""Write a sanitised SHA-256 inventory for CI-generated event evidence.

Digests provide tamper-evident content comparison, not a signed attestation.
The manifest records the commit/run supplied by GitHub Actions; local runs
are clearly labelled and are not a substitute for GitHub provenance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


def digest(path: Path) -> str:
    """Hash a regular local evidence file in bounded chunks."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("Evidence file is missing or is a symbolic link")
    hasher = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def manifest_for(paths: list[Path]) -> dict:
    names = [path.name for path in paths]
    if len(names) != len(set(names)):
        raise ValueError("Evidence basenames must be distinct")
    return {
        "schema_version": 1,
        "evidence_type": "sha256_digest_manifest",
        "cryptographically_signed": False,
        "source_commit": os.environ.get("GITHUB_SHA", "local-unverified"),
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
        "artifacts": [
            {
                "filename": path.name,
                "size_bytes": path.stat().st_size,
                "sha256": digest(path),
            }
            for path in paths
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Produce local evidence SHA-256s tied to a GitHub run if available"
    )
    parser.add_argument("--out", required=True)
    parser.add_argument("files", nargs="+")
    args = parser.parse_args(argv)
    output = Path(args.out)
    if output.exists():
        parser.error("refusing to overwrite an existing evidence manifest")
    try:
        report = manifest_for([Path(file) for file in args.files])
        with output.open("x", encoding="utf-8") as destination:
            json.dump(report, destination, indent=2)
            destination.write("\n")
    except (OSError, ValueError):
        parser.error("evidence files are missing, unsafe or unreadable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
