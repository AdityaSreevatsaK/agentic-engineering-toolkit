# ADR-0012: Local-first LangGraph RAG starter

**Status:** Accepted for M12 implementation

## Context

The Agent Project Scaffolder requires a second runnable template beyond deterministic tool routing. The target is a believable, independent LangGraph retrieval-and-answer application that can be generated, installed, tested and run on Windows/Linux without keys, hosted embedding APIs or Docker.

## Decision

- Register `langgraph-rag` in the M11 template registry, with a distinct Project Doctor profile and no changes to the existing `tool-agent` default.
- Generate a separate FastAPI service with `POST /ask`, a typed LangGraph `retrieve -> respond` graph, sample synthetic JSONL evidence and source ID responses.
- Use bounded local **BM25 lexical retrieval** implemented in Python. There are no vector embeddings or semantic similarity claims. This is nonetheless a genuine retrieval-augmented flow: query, ranked passage lookup, context assembly, and optional local model answer synthesis.
- Mock mode is deterministic and quotes the highest-scoring source. It proves retrieval/wiring rather than LLM-generation quality.
- Optional Ollama mode calls only a validated loopback HTTP endpoint. Automated tests inject fake responses, exercise error sanitisation and confirm the selected passages enter the model prompt.
- Include opt-in ingestion of small local UTF-8 .txt/.md files with deterministic chunking, bounded file sizes and refusal to overwrite existing corpora.
- Validate generated source with the read-only Project Doctor, run generated tests on Windows/Linux Python 3.11/3.12, and verify that the scaffolder wheel bundles the template.
- Do not add AEA, the historical Agent Quality Kit or third-party evaluation runtimes as mandatory generated-app dependencies.

## Limits

This is a **local developer starter**, not a public-facing retrieval service. It lacks authentication, access control, prompt-injection guarantees, persistent index infrastructure, document provenance verification, automatic embedding models and production monitoring. A model may still hallucinate or ignore citations. Do not ingest client/confidential data or deploy its API publicly as-is. Advanced application hardening belongs to M14.
