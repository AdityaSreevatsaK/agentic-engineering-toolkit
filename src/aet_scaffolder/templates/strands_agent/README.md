# __PROJECT_NAME__

Generated with AET's **AWS Strands Agent** template (provider: `__PROVIDER__`).

This is a **real Strands Agents SDK** project: `strands.Agent` hosts a decorated `@tool` for synthetic order-status lookup, and the HTTP interface invokes the SDK agent loop on every request. Two modes are supported:

| Mode | Behaviour | Prerequisites |
| --- | --- | --- |
| `mock` (default) | A tiny scripted Strands `Model` emits a tool request for `order status ORD-1001`, triggering a real Strands tool invocation. Other questions get a deterministic text reply. **This is not LLM reasoning.** | None beyond Python dependencies |
| `bedrock` | Strands uses an actual `BedrockModel` to call a model hosted on Amazon Bedrock, which may select the tool. | AWS credentials, suitable IAM policy, authorised Bedrock model access and charges |

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

The scaffolder's `--model` switch is reserved for the legacy Ollama templates; configure Strands Bedrock model ID using `AET_BEDROCK_MODEL_ID`.

## Project layout

| File | Responsibility |
| --- | --- |
| `app/main.py` | Local FastAPI `/invoke` and `/health` |
| `app/config.py` | Validated, environment-driven provider/region/model |
| `app/agent.py` | Strands Agent construction and isolated invocation |
| `app/tools.py` | Annotated synthetic `@tool`, read-only and bounded |
| `app/offline_model.py` | Deterministic Strands event source, no LLM or AWS |
| `tests/` | Actual SDK runtime checks and fake Bedrock wiring tests |

Limitations: this is a single agent with one fabricated tool; its mock provider deliberately knows how to request a single example command and makes no claim of intelligent tool planning. More complete configuration, logs, error classification, CI and deployment controls belong to M14. AEA is a separate project; this generated app does not ship any agent evaluation engine.
