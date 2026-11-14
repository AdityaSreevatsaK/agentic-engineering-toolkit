"""Bounded JSONL knowledge loading; no implicit HTTP calls or document execution."""
import json
import os
from time import sleep
from functools import lru_cache
import re
from dataclasses import dataclass
from pathlib import Path

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
_ROOT = Path(__file__).resolve().parent.parent
# Windows atomic file replacement may briefly block metadata/open operations.
_READ_ATTEMPTS = 8 if os.name == "nt" else 1


class KnowledgeError(ValueError):
    """Local knowledge file cannot be read safely."""


@dataclass(frozen=True)
class Document:
    id: str
    text: str


@lru_cache(maxsize=8)
def _cached_documents(
    path: str, modified_ns: int, changed_ns: int, size: int, inode: int,
) -> tuple[Document, ...]:
    """Return an immutable validated snapshot for the observed file signature."""
    del modified_ns, changed_ns, size, inode
    raw = Path(path).read_text(encoding="utf-8")
    documents: list[Document] = []
    seen: set[str] = set()
    for line in raw.splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        if not isinstance(data, dict):
            raise KnowledgeError("Knowledge record must be an object")
        doc_id, text = data.get("id"), data.get("text")
        if (
            not isinstance(doc_id, str) or not _ID.fullmatch(doc_id)
            or doc_id in seen or not isinstance(text, str)
            or not text.strip() or len(text) > 4000
        ):
            raise KnowledgeError("Invalid or duplicate knowledge document")
        seen.add(doc_id)
        documents.append(Document(doc_id, text.strip()))
        if len(documents) > 200:
            raise KnowledgeError("Knowledge corpus exceeds 200 documents")
    if not documents:
        raise KnowledgeError("Knowledge corpus is empty")
    return tuple(documents)


def load_documents(path: str | Path = "data/knowledge.jsonl") -> list[Document]:
    """Load a validated corpus; tolerate brief Windows atomic-swap read locks.

    Retrying applies only to transient missing/permission access during a
    concurrent local file replacement. Invalid JSONL, oversized corpora and
    symlinks still fail closed without retrying. No stale fallback is served.
    """
    target = Path(path).expanduser()
    if not target.is_absolute():
        target = _ROOT / target
    for attempt in range(_READ_ATTEMPTS):
        try:
            if target.is_symlink():
                raise KnowledgeError("Knowledge file is missing or is a symbolic link")
            if not target.is_file():
                raise FileNotFoundError("Knowledge file is temporarily unavailable")
            stat = target.stat()
            if stat.st_size > 1_000_000:
                raise KnowledgeError("Knowledge file exceeds 1 MB")
            # Copy so callers cannot modify shared cached state. A replacement
            # between stat and open still yields one fully written file version.
            return list(_cached_documents(
                str(target), stat.st_mtime_ns, stat.st_ctime_ns,
                stat.st_size, stat.st_ino,
            ))
        except (PermissionError, FileNotFoundError) as exc:
            if attempt + 1 < _READ_ATTEMPTS:
                sleep(0.01)
                continue
            raise KnowledgeError("Knowledge file is unreadable or invalid JSONL") from exc
        except (OSError, UnicodeError, ValueError) as exc:
            if isinstance(exc, KnowledgeError):
                raise
            raise KnowledgeError("Knowledge file is unreadable or invalid JSONL") from exc
    raise KnowledgeError("Knowledge file is unreadable or invalid JSONL")
