# Agentic Engineering Toolkit (AET)

**Status:** M6 local-first reference prototypes; not production-ready. **Privacy:** This repository must remain private.

Three independently installable developer-facing building blocks:
1. **Agent Project Scaffolder** — native-Windows-compatible FastAPI/LangGraph generation, deterministic tool-routing example, optional local Ollama text provider, project doctor and microbenchmark.
2. **Agent Quality Kit** — deterministic tool traces, assertion helpers, output contracts and pytest integration, independent of agent frameworks.
3. **Portable Provider Contract** — typed text-only inference protocol, deterministic mock, loopback-only Ollama adapter and a bridge to existing generated projects. It has no mandatory SDK dependencies.

## Agent Project Scaffolder

From this repository, with Python 3.11+:

```powershell
python -m pip install -e .
agentkit list
agentkit new demo-agent --provider mock
agentkit doctor demo-agent
cd demo-agent
python -m pip install -e ".[dev]"
python -m pytest -q
python -m uvicorn app.main:app --reload
```

Try `http://127.0.0.1:8000/docs` and `POST /invoke` with `{"question":"order status ORD-1001"}`. This uses entirely synthetic data. For optional local inference, see `agentkit new local-agent --provider ollama --model llama3.2:1b`. Real inference requires a separate local Ollama install/model download.

## Standalone Agent Quality Kit

```powershell
python -m pip install -e "./packages/agent-quality-kit[dev]"
python -m pytest packages/agent-quality-kit/tests -q
```

[Quality Kit documentation](packages/agent-quality-kit/README.md); independent generated-app integration in `examples/quality-kit-demo`.

## Portable Provider Contract (M6)

```powershell
python -m pip install -e "./packages/agent-provider-contract[dev]"
python -m pytest packages/agent-provider-contract/tests -q
```

[Provider package reference](packages/agent-provider-contract/README.md) and [architecture mapping](docs/architecture/provider-portability.md). The AWS, Azure and Google Cloud sections are **proposals**, not integrated or tested cloud backends. CI tests the mock and fake local Ollama provider, and a compatibility bridge to generated projects.

## Developer productivity evidence

`agentkit-benchmark --runs 10 --warmups 2 --provider mock` reports file generation and static validation timings. This does **not** measure saved developer effort; see `docs/benchmarks/study_protocol.md` for the controlled study design.

## Verification and restrictions

Private GitHub Actions tests all three independently installable packages, generated project behavior and installed wheels across Windows/Linux Python 3.11/3.12. **No cloud accounts, paid APIs, model downloads or WSL are needed for the standard CI matrix.** All fixtures are synthetic. The generated HTTP API has no authentication and must not be exposed publicly; never commit real credentials, client material or employer-owned code without permission.
