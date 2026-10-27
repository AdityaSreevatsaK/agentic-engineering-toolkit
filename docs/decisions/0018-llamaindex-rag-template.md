# ADR-0018: Offline-native LlamaIndex RAG template

Status: Proposed in M18; production adoption depends on further validation.

## Motivation

AET has LangGraph and Strands examples. Developer teams also use LlamaIndex for knowledge retrieval. Providing a genuine SDK-native starter improves scaffold choice without rewriting existing templates or introducing a redundant orchestration wrapper.

## Decision

- Add a fourth, separately self-contained `llamaindex-rag` template to the registry.
- Use `llama_index.core.SimpleKeywordTableIndex` and `as_retriever(retriever_mode="simple")` to index bounded local JSONL passages on demand, with a `MockLLM` explicitly supplied to avoid implicit default OpenAI SDK resolution. Offline mock response includes the source passage, not a simulated model-generated answer.
- Keep existing `tool-agent`, `langgraph-rag`, `strands-agent` and their registered validation profiles unchanged.
- Support optional native LlamaIndex LLM integrations for loopback Ollama, OpenAI, Azure OpenAI, Anthropic and Bedrock Converse. Import SDKs only after explicit selection, use SDK-native credential handling and no hardcoded secrets.
- Retain generated FastAPI foundations, sanitised failures, conservative readiness, synthetic knowledge, independent tests, Docker/CI references and read-only Project Doctor.
- Run an actual generated-app native LlamaIndex offline suite, plus packaging and structural tests, across Ubuntu/Windows Python 3.11/3.12, without any cloud API keys or billable calls.

## Boundaries

- Keyword lookup is not vector/semantic retrieval, BM25, document access control or production knowledge ingestion.
- No true agent loop, distributed persistence, streaming, authentication, tenant isolation, token-budget management or prompt-injection guarantees.
- Rebuilding the small local index per request is deliberate; larger corpora need an approved persistent indexing architecture.
- Passing offline tests does not prove real cloud model compatibility, adoption or productivity improvement.

## Merge dependency

M16 and M17 independently update shared provider registry/generator files. M18 must remain isolated until those milestones merge, then be reconciled against current master, fully retested and only then merged.
