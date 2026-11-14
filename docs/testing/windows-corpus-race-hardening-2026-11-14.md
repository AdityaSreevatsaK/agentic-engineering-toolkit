# Intermittent Windows RAG corpus-update event: investigation and hardening

**Date:** 14 November 2026. **Product:** AET Agent Project Scaffolder only. **Branch:** `fix/diagnose-windows-rag-corpus-race`. This is an evidence-based investigation of a synthetic offline CI scenario, not a production incident or a confirmed cloud-provider defect.

## Verified history and isolation

- Following [PR #40](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/pull/40), protected `master` advanced to `9bce484ae1bbed349f390195f69aaf92fc97f910`.
- [Post-merge CI run #43591733751](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions/runs/43591733751), first attempt: the **Windows Server 2025 / Python 3.12** `smoke` job failed. All four other required jobs passed.
- The complete [failed deep-event evidence artifact 14112413523](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions/runs/43591733751/artifacts/14112413523) recorded **715/716 passing scenarios, 22/23 passing template/provider pairs**. The **single** failure was `langgraph-rag / openai / concurrent_atomic_corpus_updates`, with synthetic scenario status **503**.
- This pairing is configured for OpenAI but forced by the test harness to **local mock** inference. No OpenAI API calls were executed.
- [Rerun of the failed job](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions/runs/43591733751) passed, making the run's latest attempt **5/5**. The failure has *intermittent* symptoms; a successful rerun alone does not explain it.

## What the initial failure proved, and what it did not

The race scenario starts a thread that atomically alternates the local JSONL corpus between two complete valid states, while 12 HTTP TestClient requests read it through four workers. The test requires the writer to complete, no atomic replacements to fail, and **all 12 requests to return HTTP 200**. The failing synthetic `503` can be set when any request fails; the scenario can also fail solely due to the writer or deadline, in which case the synthetic status could still be 200.

**Evidence limitation:** The original event did not separately retain `writer_completed`, `atomic_replace_failed`, or the number of non-200 responses. Therefore we **cannot conclude** whether this occurrence was caused by a transient Windows file-sharing denial, an application read error, or an unfinished writer. Do not label it a fixed application bug without more evidence.

The Windows atomic-swap helper already retried `PermissionError` up to **30 times with 10 ms delays**. Historical [5 November deep-event report](deep-event-sweep-2026-11-05.md) established genuine Windows sharing-denial behaviour, making this retry a plausible point to harden, but not proof of this failure's exact cause.

## Proposed scoped changes and strict acceptance

1. Extend the synthetic writer's bounded retry from 30 to **100 attempts**, each with a 10 ms delay; apply retries only to Windows `PermissionError`, propagate persistent denial or any other OS failure, and always clean temporary candidates. This never silently ignores a failed update, and does not change generated-app code.
2. Add allowlisted event diagnostics: `writer_completed` (Boolean), `atomic_replace_failed` (Boolean), and `non_200_response_count` (bounded integer). Add these fields to failure JSONL via explicit typing only, never raw exception text, paths, request/response bodies or credentials.
3. Add standard-library-based root regression tests for transient and persistent synthetic Windows denials, non-Windows error handling, and sanitised JSON failure propagation.
4. On **Windows Python 3.12 only**, repeat the exact generated `langgraph-rag` / `openai` offline child scenario **eight times**, with unique project directories and a sanitised machine-readable artifact. The RAG model remains mock. A trial fails if any of its original scenarios fails; no accepted-response or event assertion is relaxed. This extra run executes even if the preceding deep-event test fails, so diagnostic evidence is retained.
5. Keep the five required GitHub check names, four OS/Python matrix legs, 23-pair matrix, 716-case deep-event suites, four Docker image probes and Windows sequential isolated installs. No new workflow, cloud traffic or paid inference.

## Validation gates and caveats

- Require all five checks on the **final PR head**, and inspect the actual eight-trial artifact. If any trial fails, investigate its specific Boolean/count combination before merging; do not keep blindly increasing retry delays.
- Require the rerun/post-merge `master` checks and report exact results. An eight-trial passing stress run reduces uncertainty but **does not establish a mathematical absence of intermittent failure**.
- No production authentication, security testing against live providers, sustained load, or multi-team adoption is demonstrated by this fix.
- Compare the scope of new evidence with the previously recorded `715/716` failure and successful rerun; do not rewrite history.

**Initial status:** The observed historical failure and successful rerun were verified through GitHub's linked run, decoded job log and downloaded JSON evidence. Proposed code and tests are pending new CI verification at the time of writing.
