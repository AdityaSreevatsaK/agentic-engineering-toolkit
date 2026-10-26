# M15: Independent AET adoption trial

**Status: Protocol ready, no independent trials conducted.** This document defines what an unfamiliar engineer must accomplish without assistance. It is not proof of adoption or reduced setup time.

## Purpose and predeclared acceptance

Hypothesis: an engineer who has not worked on AET can independently generate, understand, run and make one meaningful change to a working agent application.

**Primary outcome:** the reviewer completes the LangGraph RAG exercise below from a fresh clone and demonstrates two successful HTTP requests (original corpus and amended synthetic corpus), with passing generated tests and no author intervention.

**Secondary outcomes:** active time spent on steps after prerequisites, number of manual fixes, clarity of documentation, and critical blockers. Dependency download/wall-clock wait is recorded separately and not mistaken for developer effort.

Pilot targets, not achieved results:
- Obtain at least **two** independent, consenting reviewers; with this sample, findings remain exploratory.
- Aim for **both reviewers** completing the primary outcome without live help, and **zero critical security or functionality blockers**.
- Record every failure, incomplete attempt, prior framework experience and deviations from instructions.
- **Do not claim a percentage reduction in developer hours** from this exercise. That requires the separate matched manual-vs-scaffolder protocol in [M4 study protocol](../benchmarks/study_protocol.md) and [M8 analyser](../pilot/README.md).

## Prerequisites and ethics

Obtain any needed organisation/project approval before inviting reviewers or using company equipment. This public repository is a personal technical prototype, not an employer-endorsed product. Use only **synthetic** data. No credentials, client files, private project outputs, customer information or identifiable participant responses should enter this public repository.

Reviewer prerequisites: Python 3.11 or 3.12, Git, permission to install public Python packages, an internet connection for installation, and Windows or Linux. Run each project locally; no cloud account, API key, Docker or Ollama is required. Preinstallation and connection issues are logged separately.

An observer should provide only these instructions, record elapsed active time and interventions, and avoid coaching. The owner of AET is **not** an independent reviewer.

## Primary trial: LangGraph RAG

Start from a fresh checkout using a unique empty work directory:

```powershell
git clone https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit.git
cd agentic-engineering-toolkit
python -m pip install -e .
python scripts/adoption_preflight.py
agentkit list
agentkit new pilot-rag --template langgraph-rag --provider mock
agentkit doctor pilot-rag
cd pilot-rag
python -m pip install -e ".[dev]"
python -m pytest -q
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The preflight output is **machine-only structural evidence**, not an independent user result. Run it before the timed tasks; do not count its machine runtime as human time saved. The reviewer may consult the generated README and standard documentation, but must log any manual fixes or intervention.

Use `http://127.0.0.1:8000/docs` to submit **POST /ask** with this JSON:

```json
{"question": "What is the sample return policy?"}
```

Expected: HTTP 200, `source_ids` includes `returns`, and the answer mentions the 30-day sample policy. No live model is contacted in mock mode.

Stop the server if necessary, then append exactly this **synthetic** line to `data/knowledge.jsonl`:

```json
{"id":"violet-manual","text":"Violet reference manuals are indexed on Thursday."}
```

Restart the server, submit:

```json
{"question": "Which day are violet reference manuals indexed?"}
```

Expected: HTTP 200, `source_ids` contains `violet-manual`, and the mock answer includes `Thursday`. This demonstrates that the developer can alter the local corpus and observe a behaviour change, not just run the starter as-is. Run `python -m pytest -q` again after editing.

**Completion rule:** tests pass, both requests are verified, and the new record changes retrieved evidence. Merely generating files, passing Project Doctor or running CI is not a completed independent trial.

## Optional secondary trials (record separately)

**Tool Agent:** in a fresh project, `agentkit new pilot-tools --template tool-agent --provider mock`, run Doctor, install `".[dev]"`, run tests, start the API and send `POST /invoke` with `{"question":"order status ORD-1001"}`. The answer must report the synthetic shipped status.

**Strands Agent:** same sequence using `--template strands-agent --provider mock`. This exercises the actual Strands SDK agent loop and its synthetic tool, but the offline provider is scripted and does not demonstrate autonomous reasoning.

Treat optional tasks as distinct trial observations. Do not force reviewers to complete all three or interpret partial coverage as three-team adoption.

## Record and report findings

Use the blank [reviewer observation form](reviewer-notes-template.md) stored outside the public repo in an approved place. Capture the chosen template, outcome, actual hands-on minutes, elapsed downloads, manual fixes, any observer help, test outcome and blockers.

Keep participant notes private/approved. Share only an explicitly reviewed, anonymised aggregate, with counts and limitations. The [M15 evidence register](evidence-register.md) distinguishes machine proof, human usability, adoption and measured savings.

Do **not** recruit participants, fabricate their observations, infer team adoption from repository stars, or publish timing reductions without the matched controlled study.
