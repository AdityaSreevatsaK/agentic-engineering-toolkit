# Agentic Engineering Toolkit (AET)

**Status:** M1 prototype, not production-ready. **Visibility:** Keep this repository private.

A local-first collection of independently reusable agent engineering assets. M1 builds the **agent project scaffolder**: generate a testable FastAPI + LangGraph project with a deterministic mock implementation, then opt into a local LLM later.

## Prerequisites

- Python 3.11+ (native Windows, WSL2, Linux and macOS)
- pip for installation; Docker and cloud accounts are **not** required

## Create a project

```powershell
python -m pip install -e .
agentkit new demo-agent --template tool-agent --provider mock
cd demo-agent
python -m pip install -e ".[dev]"
python -m pytest
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for API documentation. The mock workflow does not call a model or external network. On Windows, use PowerShell, Command Prompt or PyCharm's terminal; WSL is optional.

### Verify the scaffolder itself

```powershell
python -m pip install pytest
python -m pytest
```

## Boundaries

- Initial template: `tool-agent` with `mock` provider. Unknown providers/templates fail explicitly.
- The generated application uses LangGraph for local orchestration and FastAPI for HTTP transport.
- M1 is a deterministic workflow skeleton, not yet an LLM-driven tool-calling agent.
- Generated code is offline at runtime (once dependencies are installed). Never commit secrets or client data.
- GitHub Actions on private repositories executes code on GitHub-hosted machines, not on your laptop.
- Upcoming: Copier-based template lifecycle, local Ollama adapter, evaluation package, broader provider contracts, and portability reference.

## Repository structure

- `src/aet_scaffolder`: generator CLI and bundled template
- `tests`: scaffolder smoke tests
- `.github/workflows`: Linux + Windows CI
- `docs/decisions`: architecture decision records

License and employer IP approval must be decided before external distribution. No public publication is authorised.
