"""Verify LlamaIndex retrieval genuinely indexes documents without remote services."""
from app.knowledge import Document
from app.retrieval import retrieve


def test_retrieval_uses_keyword_content_and_preserves_source_identity():
    docs = [
        Document(id="returns", text="Return refunds are processed within 30 days."),
        Document(id="shipping", text="Packages ship in two business days."),
    ]
    results = retrieve("How does a return refund work?", docs, top_k=2)
    assert results
    assert results[0].id == "returns"


def test_unrelated_query_returns_no_results():
    docs = [Document(id="returns", text="Returns accepted after delivery.")]
    assert retrieve("astronomy supernova", docs, top_k=2) == []


def test_results_are_bounded_by_top_k():
    docs = [Document(id=f"policy-{i}", text=f"Sample returns apply to order {i}")
            for i in range(5)]
    assert len(retrieve("returns", docs, top_k=2)) <= 2


def test_native_keyword_index_cache_invalidates_on_document_change():
    from app.retrieval import _index_for_documents
    _index_for_documents.cache_clear()
    first_docs = [Document(id="unique-first", text="Rare saffron reminder")]
    assert retrieve("saffron", first_docs, top_k=1)
    before = _index_for_documents.cache_info()
    assert retrieve("saffron", list(first_docs), top_k=1)
    assert _index_for_documents.cache_info().hits == before.hits + 1
    new_docs = [Document(id="unique-second", text="Rare violet reminder")]
    hits = retrieve("violet", new_docs, top_k=1)
    assert hits and hits[0].id == "unique-second"
    assert _index_for_documents.cache_info().misses == before.misses + 1


def test_native_keyword_index_rejects_invalid_top_k():
    import pytest
    with pytest.raises(ValueError, match="top_k"):
        retrieve("returns", [Document("sample", "returns accepted")], 0)
