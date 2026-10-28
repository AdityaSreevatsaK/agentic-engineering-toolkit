# M19: Fresh-user walkthrough (independent trial, not completed evidence)

A reviewer must be unfamiliar with the implementation, use only these
instructions and the generated project's README, and not receive coaching
from its author. Obtain consent and required organisational authorisation
before any real trial. Use **synthetic test data only**; never commit
credentials, participant identities, client documents or internal source code.

## Prerequisites

Windows PowerShell or Linux, Python 3.11/3.12, Git, and access to a Python
package index for one-time installation. No Docker, WSL, model download, cloud
keys or paid API calls. Record prerequisites and download wait separately from
active task time. Record failures and deviations; do not silently fix results.

## Task A: generate and run a RAG service

From a new workspace (not a previously installed AET environment), create
and activate a Python virtual environment per your local policy, then run:

~~~powershell
git clone https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit.git
cd agentic-engineering-toolkit
python -m pip install -e .
agentkit list
agentkit new pilot-rag --template langgraph-rag --provider mock
agentkit doctor pilot-rag
cd pilot-rag
python -m pip install -e ".[dev]"
python -m pytest -q
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
~~~

In a browser, open http://127.0.0.1:8000/docs and submit POST `/ask`:

~~~json
{"question":"What is the sample return policy?"}
~~~

Expected: HTTP 200; `source_ids` contains `returns`; answer includes
the fictional 30-day return window. Keep this server running.

## Task B: change the outcome without changing source code

In a **second terminal**, navigate to the generated `pilot-rag` directory,
not `src/aet_scaffolder/templates`. Print the exact absolute file path:

~~~powershell
python -c "from pathlib import Path; print(Path('data/knowledge.jsonl').resolve())"
~~~

Open that file and append a new synthetic record on its own line:

~~~json
{"id":"violet-manual","text":"Violet reference manuals are indexed on Thursday."}
~~~

Save it and call POST `/ask` again, now with:

~~~json
{"question":"Which day are violet reference manuals indexed?"}
~~~

Expected: HTTP 200, `source_ids` contains `violet-manual`, and the
answer includes `Thursday`. The API reloads the corpus on each request,
so **no server restart is needed**. Run the generated tests again.
If you must stop the server, use **Ctrl+C** in the Uvicorn terminal, then
run the Uvicorn command again on its own line from `pilot-rag`.

Record whether the participant completed both tasks independently, how much
active work was needed, waiting time, manual fixes, observer interventions
and any blockers. An observer's instructions after a blockage count as an
intervention, not independent success.

## Optional Task C: framework alternatives

These are separate optional trials, not four independent team adoptions.
Generate each in an empty named directory from the AET checkout:

| Template | Generate | API | Expected result |
| --- | --- | --- | --- |
| `tool-agent` | `agentkit new trial-tool --template tool-agent --provider mock` | POST `/invoke` `{"question":"order status ORD-1001"}` | Synthetic shipped status, tool used |
| `strands-agent` | `agentkit new trial-strands --template strands-agent --provider mock` | POST `/invoke` same request | Actual SDK tool loop, scripted offline model |
| `llamaindex-rag` | `agentkit new trial-index --template llamaindex-rag --provider mock` | POST `/ask` `{"question":"What is the sample return policy?"}` | Native keyword retrieval, returns source ID |

For each, run `agentkit doctor NAME`, `cd NAME`,
`python -m pip install -e ".[dev]"`, `python -m pytest -q`, and
`python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`.
Start only one server at a time to avoid port conflicts. The API has no
authentication; bind exclusively to 127.0.0.1.

## Evidence and honest boundaries

This task shows only that a person could complete the documented local
exercise, not that the service is production-secure, semantically accurate,
cloud-ready or adopted by a delivery team. A matched manual baseline with
balanced order is required for a causal time-saving claim. Do not publish
raw notes or participant-level timing in this public repository. Record an
anonymous coded result in an approved private system and share only
authorised, reviewed aggregates.
