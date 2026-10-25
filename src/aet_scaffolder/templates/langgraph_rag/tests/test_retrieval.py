"""Deterministic offline retrieval and knowledge validation tests."""
import json

import pytest

from app.knowledge import Document, KnowledgeError, load_documents
from app.retrieval import search


def test_load_sample_docs():
    docs = load_documents()
    assert {d.id for d in docs} == {"returns", "shipping", "support"}
    assert all(d.text for d in docs)


def test_bm25_returns_relevant_evidence_and_is_repeatable():
    docs = load_documents()
    hits = search("What is the return policy?", docs, top_k=2)
    assert hits
    assert hits[0].document.id == "returns"
    assert all(hit.score > 0 for hit in hits)
    assert [h.document.id for h in hits] == [
        h.document.id for h in search("What is the return policy?", docs, top_k=2)
    ]


def test_no_overlap_returns_no_evidence():
    assert search("astrophysics nebula", load_documents()) == []


def test_tie_break_by_source_id():
    docs = [Document("z", "delivery"), Document("a", "delivery")]
    assert [x.document.id for x in search("delivery", docs)] == ["a", "z"]


def test_invalid_top_k_is_rejected():
    with pytest.raises(ValueError, match="top_k"):
        search("policy", load_documents(), top_k=0)


def test_reject_duplicate_and_malformed_corpus(tmp_path):
    path = tmp_path / "knowledge.jsonl"
    path.write_text(
        json.dumps({"id": "duplicate", "text": "first"}) + "\n" +
        json.dumps({"id": "duplicate", "text": "second"}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(KnowledgeError, match="duplicate"):
        load_documents(path)
    path.write_text("{bad", encoding="utf-8")
    with pytest.raises(KnowledgeError):
        load_documents(path)


def test_reject_symbolic_link(tmp_path):
    real = tmp_path / "real.jsonl"
    real.write_text('{"id":"safe","text":"synthetic"}\n', encoding="utf-8")
    link = tmp_path / "linked.jsonl"
    try:
        link.symlink_to(real)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation is unavailable")
    with pytest.raises(KnowledgeError, match="symbolic link"):
        load_documents(link)
