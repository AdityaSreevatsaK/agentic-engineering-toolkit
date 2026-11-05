"""Real, deterministic BM25 lexical retrieval, with no hosted embedding dependency."""
import math
import re
from functools import lru_cache
from collections import Counter
from dataclasses import dataclass

from .knowledge import Document

_WORD = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _WORD.findall(text.lower())


@dataclass(frozen=True)
class SearchHit:
    document: Document
    score: float


@lru_cache(maxsize=8)
def _corpus_stats(
    documents: tuple[Document, ...],
) -> tuple[tuple[Counter, ...], tuple[int, ...], float]:
    """Reuse immutable lexical statistics for identical document snapshots."""
    counts = tuple(Counter(tokenize(doc.text)) for doc in documents)
    lengths = tuple(sum(count.values()) for count in counts)
    avg = sum(lengths) / len(lengths) if lengths else 1.0
    return counts, lengths, avg or 1.0


def search(query: str, documents: list[Document], *, top_k: int = 2) -> list[SearchHit]:
    """Return relevant documents ranked by BM25; zero-overlap hits are excluded."""
    if not 1 <= top_k <= 5:
        raise ValueError("top_k must be between 1 and 5")
    tokens = set(tokenize(query))
    if not tokens or not documents:
        return []
    counts, lengths, average_length = _corpus_stats(tuple(documents))
    df = {term: sum(term in count for count in counts) for term in tokens}
    hits: list[SearchHit] = []
    for document, count, length in zip(documents, counts, lengths):
        score = 0.0
        for term in tokens:
            frequency = count[term]
            if not frequency:
                continue
            idf = math.log(1 + (len(documents) - df[term] + 0.5) / (df[term] + 0.5))
            score += idf * frequency * (1.5 + 1) / (
                frequency + 1.5 * (1 - 0.75 + 0.75 * length / average_length)
            )
        if score > 0:
            hits.append(SearchHit(document, score))
    return sorted(hits, key=lambda h: (-h.score, h.document.id))[:top_k]
