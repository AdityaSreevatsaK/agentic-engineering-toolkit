"""Native LlamaIndex lexical indexing/retrieval; never loads embedding models."""
from llama_index.core import SimpleKeywordTableIndex
from llama_index.core.llms import MockLLM
from llama_index.core.schema import TextNode

from .knowledge import Document


def retrieve(question: str, documents: list[Document], top_k: int) -> list[Document]:
    """Build a bounded transient index and return source documents in retriever order.

    The explicit MockLLM prevents LlamaIndex from resolving its default OpenAI LLM.
    SimpleKeywordTableIndex uses regex-based keywords rather than model inference.
    """
    nodes = [TextNode(id_=document.id, text=document.text) for document in documents]
    index = SimpleKeywordTableIndex(nodes, llm=MockLLM(max_tokens=64))
    results = index.as_retriever(
        retriever_mode="simple", num_chunks_per_query=top_k
    ).retrieve(question)
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
