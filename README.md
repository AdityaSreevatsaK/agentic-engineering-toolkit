# Agentic Engineering Toolkit (AET)

**Status:** M4 evidence-collection prototype; not production-ready. **Privacy:** Keep this repository private.

A local-first scaffolder for creating testable FastAPI + LangGraph agent projects. Configure deterministic mock responses or optional local Ollama text generation. **Core functionality does not require WSL, Docker, or cloud accounts.**

## Quick start (native Windows PowerShell or PyCharm terminal)

```powershell
python -m pip install -e .
agentkit --version
agentkit list
agentkit new demo-agent --provider mock
agentkit doctor demo-agent
cd demo-agent
python -m pip install -e ".[dev]"
python -m pytest -q
python -m uvicorn app.main:app --reload
```

Visit http://127.0.0.1:8000/docs and send `{"question":"order status ORD-1001"}` to POST /invoke. This calls a synthetic local tool. An ordinary question such as `{"question":"hello"}` uses the mock response provider.

## Development helpers

- `agentkit list` — list supported templates and providers.
- `agentkit doctor <generated-project-path>` — check required files, configuration, project metadata, and Python syntax *without importing or running generated code*.
- `agentkit doctor <path> --json` — machine-readable checks for local automation; exit status 0 on success, 1 for validation failures.
- `agentkit --version` — print installed scaffolder version.

Project validation is deliberately static. It is **not** a replacement for `pytest`, dependency vulnerability checks, authentication tests, or a real-model smoke test.

## Optional local Ollama mode

```powershell
agentkit new local-agent --provider ollama --model llama3.2:1b
agentkit doctor local-agent
cd local-agent
python -m pip install -e ".[dev]"
python -m pytest -q
```

To run inference, install Ollama separately, download your chosen model (for example `ollama pull llama3.2:1b`), and run `python -m uvicorn app.main:app --reload`. No real models are downloaded in automated CI. The local Ollama API must use a loopback address and explicit port.

## CI and distribution

Private GitHub Actions checks generate, inspect, install, and test both provider variants on Windows and Linux, Python 3.11 and 3.12. M3 also builds a wheel, installs it (not editable), generates another project from the packaged templates, and validates it with `agentkit doctor`. This specifically guards against missing template files in built distributions.

The repository is private; avoid committing real secrets or proprietary/client data without approval. The development API is unauthenticated and should not be exposed publicly. Ollama provides text responses only; model-driven tool selection, enterprise security and cloud portability remain out of scope.

## M4: Measured generator performance

Run `agentkit-benchmark --runs 10 --warmups 2 --provider mock --json-out timings.json --csv-out timings.csv` to measure project generation and static validation locally. See `docs/benchmarks/study_protocol.md` for the separate human developer comparison. **No developer time savings have been established yet.**
