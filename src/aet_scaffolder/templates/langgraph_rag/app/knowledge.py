"""Bounded JSONL knowledge loading; no implicit HTTP calls or document execution."""
import json
import re
from dataclasses import dataclass
from pathlib import Path

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
_ROOT = Path(__file__).resolve().parent.parent


class KnowledgeError(ValueError):
    """Local knowledge file cannot be read safely."""


@dataclass(frozen=True)
class Document:
    id: str
    text: str


def load_documents(path: str | Path = "data/knowledge.jsonl") -> list[Document]:
    """Read a local JSONL corpus, rejecting links, oversized or malformed content."""
    target = Path(path).expanduser()
    if not target.is_absolute():
        target = _ROOT / target
    if target.is_symlink() or not target.is_file():
        raise KnowledgeError("Knowledge file is missing or is a symbolic link")
    try:
        if target.stat().st_size > 1_000_000:
            raise KnowledgeError("Knowledge file exceeds 1 MB")
        raw = target.read_text(encoding="utf-8")
        documents: list[Document] = []
        seen = set()
        for line in raw.splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            if not isinstance(data, dict):
                raise KnowledgeError("Knowledge record must be an object")
            doc_id, text = data.get("id"), data.get("text")
            if (not isinstance(doc_id, str) or not _ID.fullmatch(doc_id)
                    or doc_id in seen or not isinstance(text, str)
                    or not text.strip() or len(text) > 4000):
                raise KnowledgeError("Invalid or duplicate knowledge document")
            seen.add(doc_id)
            documents.append(Document(doc_id, text.strip()))
            if len(documents) > 200:
                raise KnowledgeError("Knowledge corpus exceeds 200 documents")
        if not documents:
            raise KnowledgeError("Knowledge corpus is empty")
        return documents
    except (OSError, UnicodeError, ValueError) as exc:
        if isinstance(exc, KnowledgeError):
            raise
        raise KnowledgeError("Knowledge file is unreadable or invalid JSONL") from exc
