"""Opt-in bounded ingestion of local text and Markdown documents into JSONL."""
import argparse
import json
import re
import sys
from pathlib import Path

from .knowledge import KnowledgeError


def chunk_text(text: str, *, limit: int = 600) -> list[str]:
    if not 100 <= limit <= 4000:
        raise KnowledgeError("Chunk limit must be between 100 and 4000")
    words = text.split()
    output, current = [], []
    for word in words:
        if len(word) > limit:
            raise KnowledgeError("Source contains a word larger than a chunk")
        next_length = len(" ".join(current + [word]))
        if current and next_length > limit:
            output.append(" ".join(current))
            current = []
        current.append(word)
    if current:
        output.append(" ".join(current))
    return output


def ingest_directory(source: str | Path, output: str | Path, *, limit: int = 600) -> int:
    """Create a new JSONL corpus from local .txt/.md files, never overwrite output."""
    src = Path(source).expanduser()
    dest = Path(output).expanduser()
    if src.is_symlink() or not src.is_dir():
        raise KnowledgeError("Input directory is missing or a symbolic link")
    if dest.exists() or dest.is_symlink():
        raise KnowledgeError("Refusing to overwrite an existing corpus")
    paths = sorted(p for p in src.iterdir() if p.suffix.lower() in {".md", ".txt"})
    if not paths or len(paths) > 30:
        raise KnowledgeError("Supply between 1 and 30 local .txt or .md files")
    records = []
    for item in paths:
        if item.is_symlink() or not item.is_file() or item.stat().st_size > 200_000:
            raise KnowledgeError("Source file is invalid, a link or exceeds 200 KB")
        slug = re.sub(r"[^a-z0-9-]", "-", item.stem.lower()).strip("-")
        if not slug:
            raise KnowledgeError("Invalid source filename")
        try:
            data = item.read_text(encoding="utf-8")
        except (UnicodeError, OSError) as exc:
            raise KnowledgeError("Source must be readable UTF-8 text") from exc
        for index, chunk in enumerate(chunk_text(data, limit=limit), start=1):
            records.append({"id": f"{slug[:60]}-{index:03d}", "text": chunk})
    if not records or len(records) > 200 or len({r["id"] for r in records}) != len(records):
        raise KnowledgeError("Resulting corpus is empty, too large or has duplicate IDs")
    payload = "".join(json.dumps(record, ensure_ascii=True) + "\n" for record in records)
    if len(payload.encode("utf-8")) > 1_000_000:
        raise KnowledgeError("Resulting corpus exceeds 1 MB")
    try:
        with dest.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
    except OSError as exc:
        raise KnowledgeError("Cannot write new output corpus") from exc
    return len(records)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local RAG JSONL corpus")
    parser.add_argument("--input", required=True, help="Local directory containing .txt and .md files")
    parser.add_argument("--output", required=True, help="NEW output JSONL path")
    args = parser.parse_args(argv)
    try:
        count = ingest_directory(args.input, args.output)
    except KnowledgeError as exc:
        print(f"Ingestion failed: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {count} passages to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
