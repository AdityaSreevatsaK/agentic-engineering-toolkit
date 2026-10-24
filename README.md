# Agentic Engineering Toolkit (AET)

**Status:** M2 implementation, under validation. **Visibility:** This repository is private.

An independently reusable, local-first toolkit for generating testable agentic applications. M2 extends the project scaffolder to let developers select either deterministic mock behavior or optional local Ollama text generation. No AWS/Azure/GCP dependency, API key or WSL is required.

## Install and generate (Windows PowerShell or PyCharm terminal)

```powershell
python -m pip install -e .
agentkit new demo-agent --template tool-agent --provider mock
cd demo-agent
python -m pip install -e ".[dev]"
python -m pytest
python -m uvicorn app.main:app --reload
```

Visit http://127.0.0.1:8000/docs. POST /invoke with `{"question":"order status ORD-1001"}` executes the synthetic local order tool; with `{"question":"hello"}` the mock provider returns a deterministic response.

### Optional local Ollama project

From the repository root:

```powershell
agentkit new local-agent --template tool-agent --provider ollama --model llama3.2:1b
cd local-agent
python -m pip install -e ".[dev]"
python -m pytest
```

Then install and run Ollama on your own machine, run `ollama pull llama3.2:1b`, and start the API with `python -m uvicorn app.main:app --reload`.

The generated `.env.example` documents `AET_PROVIDER`, `AET_OLLAMA_MODEL`, `AET_OLLAMA_BASE_URL`, and a timeout. Copy it to `.env` only if you want to override defaults. **Ollama is optional.** All CI tests stub local HTTP and run without model downloads.

## Local verification

```powershell
python -m pip install pytest
python -m pytest tests -q
```

CI additionally generates and tests both provider configurations on Windows and Linux using Python 3.11 and 3.12.

## Architecture and boundaries

- `src/aet_scaffolder`: independent CLI and bundled project template.
- `app/config.py` in generated projects: validated settings and loopback-only local endpoint policy.
- `app/providers.py`: minimal mock/Ollama provider contract.
- `app/workflow.py`: LangGraph orchestration, including deterministic synthetic tool routing.
- `docs/decisions`: architecture decision records.

The Ollama adapter supports **text generation only**, not general LLM tool calling. Model output is not guaranteed deterministic. This development example is not secured for public hosting, has no persistence, and makes no claims of production readiness or verified cloud portability.

Keep company/client data and secrets out of this personal repository unless separately authorised; do not publish without explicit approval.
