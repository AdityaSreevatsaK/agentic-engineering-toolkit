# Portable Agent Provider Contract

This separately installable **text-generation-only** reference library defines a normalized synchronous request/response and provider protocol. It includes a deterministic mock, a loopback-only Ollama adapter, and a compatibility bridge for existing AET-generated `generate(str) -> str` providers.

It has **zero mandatory external Python dependencies**, no cloud SDKs, and no network requests when used with the mock. It's meant for local tests and architecture demonstrations, not for public or production deployment.

## Install (Windows PowerShell or PyCharm terminal)

From the private monorepo root:

```powershell
python -m pip install -e "./packages/agent-provider-contract[dev]"
python -m pytest packages/agent-provider-contract/tests -q
```

## Contract and mock

```python
from aet_provider import GenerateRequest, MockProvider, assert_provider_contract

model = MockProvider()
assert_provider_contract(model, expected_provider="mock")
print(model.generate(GenerateRequest("hello")).text)
```

## Optional local Ollama

```python
from aet_provider import GenerateRequest, OllamaProvider

model = OllamaProvider(model="llama3.2:1b")  # loopback-only http://127.0.0.1:11434
print(model.generate(GenerateRequest("Write one sentence.")).text)
```

This example requires Ollama running locally with that model already installed. Unit and CI contract tests use fake transports and do **not** download models.

## Adapting existing projects

```python
from aet_provider import LegacyTextAdapter, GenerateRequest
from app.providers import get_provider
from app.config import Settings

existing = get_provider(Settings(provider="mock"))
adapter = LegacyTextAdapter(existing, name="generated-mock", model="generated-v0")
print(adapter.generate(GenerateRequest("hello")).text)
```

The compatibility bridge makes the contract usable with the current generated application **without modifying its runtime code**. See `examples/provider-portability-demo` for a tested integration.

## Explicit boundaries

- Contract: one bounded text prompt in, one nonempty text response out, with provider/model identity.
- Not included: tools, streaming, image input, authentication, cost/usage reporting, retries, SDK-specific features, concurrency or multi-turn history.
- Provider contract tests that actually call a provider must use **mock or injected local fake transport** in CI. A real model may require hardware, installation and separate permission.
- Loopback restriction applies only to this Ollama adapter; it does not certify networking or data governance beyond the development reference.
- Cloud mappings are architectural sketches, not deployed integrations; see `docs/architecture/provider-portability.md`.
