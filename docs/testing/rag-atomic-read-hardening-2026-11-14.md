# Windows RAG atomic corpus snapshot: reader-side hardening, 14 November 2026

## Confirmed finding

The first [PR #41](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/pull/41) completed its final-head five-check CI and eight LangGraph/OpenAI offline corpus-race trials successfully. After merge to `master` (`ef8f851fe9fc4560122880ef6616a6e881bd7b56`), [run #43628105300](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions/runs/43628105300) failed **one** Windows Server 2025/Python 3.12 deep-event scenario: `llamaindex-rag / openai / concurrent_atomic_corpus_updates`. The full matrix still passed 22/23 pairs and 715/716 scenarios.

The [failed artifact 14127113876](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions/runs/43628105300/artifacts/14127113876) provides the first definitive separation of writer and reader signals:

| Sanitised field | Value |
| --- | --- |
| `writer_completed` | `true` |
| `atomic_replace_failed` | `false` |
| `non_200_response_count` | **1 of 12** |
| Synthetic scenario status | `503` (aggregate failure marker, not necessarily the actual HTTP response code) |

The separate eight-trial LangGraph stress harness reported **8/8 successes**. Consequently, increasing the *writer's* sharing-violation retry budget alone did not eliminate this kind of failure. It was a **concurrent HTTP reader** that returned non-200 during a fully completed atomic corpus writer sequence. The actual HTTP status of that request and exact failure location were **not** captured by the original event schema; do not claim a proven root cause or live-cloud defect.

Both generated RAG implementations share an identical `app/knowledge.py` local JSONL loader. It checks path metadata, then opens the file to populate a signature-keyed cache. A local writer can swap the file between those operations on Windows. A transient `PermissionError` or `FileNotFoundError` can be converted into a sanitised 503 by their HTTP handlers. This is a **plausible mechanism**, not yet a directly captured exception from the failed CI run. Retrieval/index concurrency also exists; future status diagnostics distinguish HTTP 500 and 503 if the problem recurs.

## Corrective changes, preserving strict validation

1. **Both generated RAG templates** now retry only `PermissionError` and `FileNotFoundError` access failures for a maximum of **eight attempts, seven 10 ms delays** on Windows. On Linux, the same errors fail immediately. The change neither retries invalid JSONL/duplicate records nor accepts malformed, missing-for-longer, symlinked or oversized corpora. There is no fallback to stale cached documents; valid reads return complete validated snapshots.
2. New per-template tests inject transient sharing denial, permanent denial, temporary absence, malformed JSONL and a symlink classification. Successful transient reads must return current content; persistent failures must still raise `KnowledgeError`.
3. Existing deep-event failures now retain an allowlisted list of actual non-200 **HTTP status codes** (integer 400–599), in addition to writer-completion, replacement-failure and non-200 count signals. No request or response bodies, exception messages, file paths or secrets are recorded.
4. Windows/Python 3.12 stress now exercises `langgraph-rag` and `llamaindex-rag` under configured OpenAI with **mock inference enforced**, eight fresh trials each, **16 trials total**. Every trial still runs the full existing child scenario set, including the strict 12-reader concurrency assertion. Failure JSON remains sanitised.
5. Five required check names, 23 supported template/provider pairs, four OS/Python jobs, four Docker builds, per-template independent installs, old AET compatibility and source-only AET scope remain unchanged. The agent evaluation project AEA is untouched.

## Evidence needed before closure

- Review all five required **final-head** CI checks; a single Windows failure still blocks merging.
- Download the 16-trial stress artifact and verify **16/16 passed**, with both template names and no skipped cases.
- Verify the full Windows/Python 3.12 deep-event result reports **716/716** and all four matrix legs report the registered 23 pairs.
- If the issue recurs, inspect the newly recorded actual HTTP status codes to distinguish a likely reader `KnowledgeError` 503 from an internal 500 or another failure. Do not hide evidence by weakening event assertions or ignoring non-200 responses.
- After merging, verify the post-merge `master` run separately. Even consecutive passes cannot prove an intermittent failure impossible.

**State when authored:** Follow-up changes proposed on `fix/rag-windows-atomic-snapshot-read`; full new CI and post-merge evidence pending.
