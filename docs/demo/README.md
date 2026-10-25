# M7: Offline end-to-end demonstration

This demonstration shows the **three** separate AET assets working together: the project Scaffolder, Agent Quality Kit and Portable Provider Contract. It uses synthetic order records, a deterministic mock response and fake Ollama HTTP transport. **No cloud request, live model, network listener, credentials or model download occurs during the demo.**

## Prerequisites

Python 3.11 or 3.12, git, and a normal Python package index for one-time dependency installation. Works in native Windows PowerShell / PyCharm terminal or Linux without WSL.

From a clone of the **private** AET repository:

```powershell
python -m pip install -e ".[demo]"
python -m pip install -e "./packages/agent-quality-kit"
python -m pip install -e "./packages/agent-provider-contract"
```

Run the complete demo:

```powershell
python scripts/run_demo.py
```

For a sanitized, machine-readable record:

```powershell
python scripts/run_demo.py --json-out m7-demo-results.json
```

The output includes a successful `agentkit doctor`-equivalent validation and eight functional checks: API health, known/unknown tool calls, mock response with no tool, invalid inputs, independent typed provider contract, compatibility bridge, and fake local Ollama adapter. It runs the generated app's FastAPI `TestClient` in a **separate interpreter** and removes the temporary generated project after execution.

The sample asserts tool use through the independent Agent Quality Kit and runs the Portable Provider Contract against both its own mock and the original generated provider. The fake Ollama transport **never opens a network connection**.

## Acceptance criteria

- Demo exit status 0 and `status: passed` in its structured output
- Static validation succeeds before importing generated code
- Generated `GET /health` and `POST /invoke` behave as expected with synthetic records
- Tool-trace assertions accurately capture the known tool call, unknown record, and fallback with no call
- Typed provider protocol, legacy bridge and injected Ollama fake pass
- No local server, cloud API, Docker, WSL or downloaded model is required
- Private GitHub Actions passes the demo on Windows/Linux Python 3.11/3.12

The script **does not install dependencies automatically**. If packages are missing, it reports the prerequisites. A successful demo does **not** establish enterprise security, semantic model quality, cloud portability in practice, or productivity savings.

## Feedback and follow-up

Use [reviewer-checklist.md](reviewer-checklist.md) for an external engineer's reproducible review and [review-notes-template.csv](review-notes-template.csv) for *blank* pseudonymized feedback. No team endorsement or adoption is claimed until it actually occurs. Obtain employer approval before inviting external participants or uploading internal feedback to this personal GitHub repository.
