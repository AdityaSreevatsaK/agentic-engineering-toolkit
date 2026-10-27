# __PROJECT_NAME__

Generated with AET's **AWS Strands Agent** template (provider: `__PROVIDER__`).

This is a **real Strands Agents SDK** project: `strands.Agent` hosts a decorated `@tool` for synthetic order-status lookup, and the HTTP interface invokes the SDK agent loop on every request. Five modes are supported:

| Mode | Behaviour | Prerequisites |
| --- | --- | --- |
| `mock` (default) | A tiny scripted Strands `Model` emits a tool request for `order status ORD-1001`, triggering a real Strands tool invocation. Other questions get a deterministic text reply. **This is not LLM reasoning.** | None beyond Python dependencies |
| `bedrock` | Original Strands `BedrockModel` configuration, unchanged. | AWS SDK identity and Bedrock access |
| `openai` | Native Strands `OpenAIModel` | `OPENAI_API_KEY`, selected `AET_OPENAI_MODEL` |
| `anthropic` | Native Strands `AnthropicModel` | `ANTHROPIC_API_KEY`, `AET_ANTHROPIC_MODEL` |
| `azure-openai` | Strands `OpenAIModel` with official `AsyncAzureOpenAI` client | `AZURE_OPENAI_API_KEY` (or supported identity), deployment, HTTPS endpoint and API version |

This example is **not production-ready**. HTTP endpoints have no authentication and must stay bound to localhost. It does not provide multi-tenant security, tool access controls, tracing, cost caps or observability.

## Quick start: offline mock

Use Python 3.11+ on Windows or Linux, without AWS, Docker or WSL.

~~~powershell
python -m pip install -e ".[dev]"
python -m pytest -q
python -m uvicorn app.main:app --host 127.0.0.1 --reload
~~~

Open http://127.0.0.1:8000/docs and submit:

- POST `/invoke` with `{"question":"order status ORD-1001"}` to see `tool_used: true` and a synthetic shipped status.
- POST `/invoke` with `{"question":"hello"}` for a deterministic response without a tool call.
- GET `/health` is a liveness check only.

The SDK's per-request `Agent` instance avoids sharing conversations between requests. The offline model does **not** call a cloud service. Automated tests include a real Strands tool loop and injected fake Bedrock-model constructor.

## Optional Amazon Bedrock inference

To use an approved AWS environment:

1. Configure short-lived AWS credentials through your standard CLI profile, environment or execution role. Never commit credentials or profile contents.
2. Confirm permission for the model you intend to use (`bedrock:InvokeModel`, and any additional permissions your invocation mode requires), region access and associated cost.
3. Copy `.env.example` to `.env` and set `AET_PROVIDER=bedrock`. Set `AET_AWS_REGION` and `AET_BEDROCK_MODEL_ID` to a **model identifier actually enabled in your account and region**; the example `us.amazon.nova-lite-v1:0` is illustrative, not guaranteed available.
4. Start the same FastAPI service and call POST `/invoke`.

`agentkit new my-agent --template strands-agent --provider bedrock` generates a Bedrock-mode configuration, but **does not contact AWS during generation**. Standard CI does not send AWS requests or run live integration tests. Success in offline CI does not verify model access, pricing or real-world autonomous tool choice.

## M17: Native cloud model selection

Each cloud mode is selected explicitly at scaffolding time or in the generated `.env`:

~~~powershell
agentkit new openai-agent --template strands-agent --provider openai
cd openai-agent
python -m pip install -e ".[dev,openai]"
~~~

Set `AET_OPENAI_MODEL` and securely supply `OPENAI_API_KEY` via your normal execution environment before live inference. For Azure, install `.[azure-openai]`, then set `AET_AZURE_OPENAI_DEPLOYMENT`, `AET_AZURE_OPENAI_ENDPOINT` (bare HTTPS origin) and `AET_AZURE_OPENAI_API_VERSION`. Its SDK accepts native Azure authentication configuration. For Anthropic, install `.[anthropic]`, configure `AET_ANTHROPIC_MODEL` and securely supply `ANTHROPIC_API_KEY`. The Strands SDK owns tool-use and model integration; this project does not implement any custom API transport.

Provider dependencies are optional so fresh mock installations and CI require no API keys, external inference or paid service. Model availability and tool-calling support vary by selected deployment. Cloud inference sends user prompts and tool content to third parties; treat it as opt-in and review applicable data handling, token budgets and authorisation. The example remains unauthenticated and **must not** be directly deployed to production.

The scaffolder's `--model` switch is reserved for the legacy Ollama templates; configure Strands Bedrock model ID using `AET_BEDROCK_MODEL_ID`.

## Project layout

| File | Responsibility |
| --- | --- |
| `app/main.py` | Local FastAPI `/invoke` and `/health` |
| `app/config.py` | Validated, environment-driven provider/region/model |
| `app/agent.py` | Strands Agent construction and isolated invocation |
| `app/cloud_models.py` | Lazy OpenAI, Anthropic and Azure SDK-native integrations |
| `app/tools.py` | Annotated synthetic `@tool`, read-only and bounded |
| `app/offline_model.py` | Deterministic Strands event source, no LLM or AWS |
| `tests/` | Actual SDK runtime checks and fake Bedrock wiring tests |

Limitations: this is a single agent with one fabricated tool; its mock provider deliberately knows how to request a single example command and makes no claim of intelligent tool planning. Production-specific authentication, traffic policies and capacity controls must be provided by each adopting team. AEA is a separate project; this generated app does not ship any agent evaluation engine.

## M14 application foundations

New projects include `app/foundation.py` with a server-issued `X-Request-ID` and one JSON request log per request. Logs include only request method, fixed route category, status code and duration. **Prompts, generated answers, auth headers, query strings, client addresses, exception strings and unknown URL paths are not logged.** Use `AET_LOG_LEVEL` in `.env` to select DEBUG, INFO, WARNING or ERROR (default INFO).

`GET /health` verifies process liveness. `GET /ready` verifies the local mock mode and applicable local dependencies. It **returns 503 for live model providers** because a network call, credentials and account entitlements are not verified by this developer template. A 503 is not evidence that the live provider itself is down.

A generated `.github/workflows/ci.yml` runs offline tests on Python 3.12. A non-root Docker reference is included, with `.dockerignore` excluding environment files and local build artifacts:

~~~powershell
docker build -t aet-demo-app .
docker run --rm -p 127.0.0.1:8000:8000 aet-demo-app
~~~

The example container runs `AET_PROVIDER=mock` and must be **bound to localhost only**. Never deploy it publicly as supplied: these apps have no authentication, tenant isolation, ingress policy, network egress controls, secrets management or deployment-specific authorisation. For production adoption, teams must add and review these separately.
