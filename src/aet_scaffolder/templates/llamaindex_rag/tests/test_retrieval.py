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
