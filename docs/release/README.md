# M19: Pilot-release readiness and adoption evidence

**Status:** The automated release-smoke is testable, but the toolkit remains a
prototype, not production-approved. No independent developer trial, team reuse
or human setup-time reduction has been verified.

This kit is deliberately small: four template walkthroughs, a reproducible
offline ASGI acceptance script, one reviewer trial, and a leadership-ready
evidence summary. It does not create another framework or an evaluation engine.

## Start on a clean Windows PowerShell or Linux terminal

Use Python 3.11 or 3.12 and a permitted Python package index. No WSL, Docker,
Ollama, paid model or cloud account is required. In your approved work directory:

~~~powershell
git clone https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit.git
cd agentic-engineering-toolkit
python -m venv .venv
~~~

Activate the environment: on Windows PowerShell, run
`.venv\Scripts\Activate.ps1`; on Linux, run `source .venv/bin/activate`.
If PowerShell blocks script execution, use the environment's Python executable
directly instead of changing machine-wide execution policy. A Python virtual
environment is recommended for avoiding collisions with other Python projects.

~~~powershell
python -m pip install -e .
python scripts/adoption_preflight.py
agentkit list
~~~

**The automated acceptance script below needs each generated app's dependencies
available in the current interpreter.** Before running it from the repository
root, create the four apps in separate folders and install their development
dependencies; these commands use only the mock provider:

~~~powershell
agentkit new local-tool --template tool-agent --provider mock
agentkit new local-graph-rag --template langgraph-rag --provider mock
agentkit new local-strands --template strands-agent --provider mock
agentkit new local-index-rag --template llamaindex-rag --provider mock
python -m pip install -e "./local-tool[dev]" -e "./local-graph-rag[dev]" -e "./local-strands[dev]" -e "./local-index-rag[dev]"
python scripts/release_smoke.py
~~~

**Note:** Since all four generated projects use the local Python package name
`app`, installing them together in one environment can cause package
namespace collisions; the acceptance script intentionally executes each
generated project's `app` in its own subprocess working directory, but an
editable installation may still depend on install order. CI independently
installs each template and tests it before this acceptance. For a stricter
local check, prefer a separate virtual environment per generated project,
then run each project's `python -m pytest -q` and the explicit HTTP procedure
in [fresh-user walkthrough](fresh-user-walkthrough.md).

The script generates **fresh temporary copies** of all four templates, checks
Doctor, sends in-process HTTP requests through FastAPI TestClient in child
interpreters, and verifies a new synthetic knowledge record changes the
retrieved answer for both RAG templates. It uses no network listener and
creates no live provider inference calls. A new, sanitised local machine report
can be saved using:

~~~powershell
python scripts/release_smoke.py --json-out m19-machine-smoke.json
~~~

The script refuses to overwrite a report. Its elapsed times cover local
generation, validation and scripted API probes, **not installation, human effort
or time saved**. The CI workflow runs this after generated dependencies are
installed and stores a machine-only report per OS/Python combination. It is
not an independent review.

## For a real engineer

Give a consenting, authorised reviewer only
[fresh-user walkthrough](fresh-user-walkthrough.md) and the generated README.
Use the [blank observer form](reviewer-notes-template.md) privately to log
outcome, active work versus waiting, manual fixes, interventions and incomplete
attempts. Keep any participant information outside this public repo. The
primary RAG corpus-mutation task remains aligned with the existing M15 protocol.

## For a technical lead or promotion reviewer

See [leadership review](leadership-review.md) for the architecture, frameworks,
provider choices, evidence matrix and risks. Evidence and next-step decisions
are summarised in [release gate](release-gate.md). Obtain organisational/IP
authorisation before pilot use. A prototype's passing CI is not permission to
send sensitive data to a third-party provider.

**Promotion-friendly statement:** Built four runnable Python application
starter templates spanning LangGraph, Strands and LlamaIndex, with multiple
optional provider integrations, offline tests, Project Doctor, a synthetic
HTTP/corpus-change smoke suite and four-platform CI. Independent adoption and
developer productivity improvement remain unverified.
