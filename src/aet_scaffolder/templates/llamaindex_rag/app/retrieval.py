"""Native LlamaIndex keyword indexing/retrieval without NLTK or model downloads.

LlamaIndex's bundled regex extractor consults NLTK stopwords at runtime.
We override ONLY keyword tokenisation; index storage, retrieval, scoring and
source-node identities remain LlamaIndex-native.
"""
import re

from llama_index.core import SimpleKeywordTableIndex
from llama_index.core.indices.keyword_table.retrievers import KeywordTableSimpleRetriever
from llama_index.core.llms import MockLLM
from llama_index.core.schema import TextNode

from .knowledge import Document

_WORDS = re.compile(r"[a-z0-9]{2,}", re.IGNORECASE)
_STOPWORDS = frozenset({
    "a", "about", "after", "all", "also", "an", "and", "are",
    "as", "at", "be", "been", "by", "can", "do", "does", "for",
    "from", "has", "have", "how", "i", "in", "is", "it", "its",
    "of", "on", "or", "our", "that", "the", "their", "there", "these",
    "this", "those", "to", "was", "were", "what", "when", "where",
    "which", "who", "why", "will", "with", "you", "your",
})


def _keywords(text: str, limit: int) -> set[str]:
    """Bounded local lexical terms, no NLTK stopword download or model calls."""
    terms = (word.lower() for word in _WORDS.findall(text))
    selected: set[str] = set()
    for word in terms:
        if word not in _STOPWORDS:
            selected.add(word)
            if len(selected) >= limit:
                break
    return selected


class _OfflineSimpleRetriever(KeywordTableSimpleRetriever):
    def _get_keywords(self, query_str: str) -> list[str]:
        return sorted(_keywords(query_str, self.max_keywords_per_query))


class _OfflineKeywordIndex(SimpleKeywordTableIndex):
    def _extract_keywords(self, text: str) -> set[str]:
        return _keywords(text, self.max_keywords_per_chunk)

    def as_retriever(self, **kwargs):
        return _OfflineSimpleRetriever(self, **kwargs)


def retrieve(question: str, documents: list[Document], top_k: int) -> list[Document]:
    """Build a bounded transient native index and return native retrieved nodes."""
    nodes = [TextNode(id_=document.id, text=document.text) for document in documents]
    # Explicit MockLLM prevents default model resolution or paid API calls.
    index = _OfflineKeywordIndex(nodes, llm=MockLLM(max_tokens=64))
    results = index.as_retriever(num_chunks_per_query=top_k).retrieve(question)
    by_id = {document.id: document for document in documents}
    seen: set[str] = set()
    output: list[Document] = []
    for result in results:
        source_id = result.node.node_id
        if source_id in by_id and source_id not in seen:
            output.append(by_id[source_id])
            seen.add(source_id)
        if len(output) >= top_k:
            break
    return output
