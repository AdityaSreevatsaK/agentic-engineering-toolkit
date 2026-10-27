# __PROJECT_NAME__

Generated using AET's **llamaindex-rag** template (selected provider: `__PROVIDER__`).

This is a runnable, bounded **LlamaIndex-native keyword retrieval** reference, not a LangGraph wrapper and not an autonomous agent. It constructs `SimpleKeywordTableIndex` over a local JSONL corpus and calls LlamaIndex's simple keyword retriever for each question. No embeddings, local model download, cloud account, Docker or WSL are required for mock mode. In offline mode, the API quotes the highest-ranked matched source; **this is not LLM synthesis**. Provider selection for synthesis is optional and explicit.

## Native Windows/Linux quick start

~~~powershell
python -m pip install -e ".[dev]"
python -m pytest -q
python -m uvicorn app.main:app --host 127.0.0.1 --reload
~~~

Open http://127.0.0.1:8000/docs. `POST /ask`:

~~~json
{"question":"What is the sample return policy?"}
~~~

The result includes a sample retrieved policy and its `returns` source ID. `GET /health` reports process liveness; `GET /ready` validates offline mock configuration and the local corpus only. Readiness deliberately returns 503 for any live provider without an external connectivity check.

## Retrieval and corpus

The bundled `data/knowledge.jsonl` is fabricated, non-client data. Each line must contain `id` and `text`. The loader enforces a maximum of 200 records, 1 MB total and 4,000 characters per passage; duplicates, malformed records and symlink targets are rejected.

This is **keyword overlap retrieval**, not vector embeddings, BM25, semantic or hybrid retrieval. Index construction is local and rebuilt for each request. LlamaIndex's `MockLLM` prevents implicit OpenAI configuration during index construction; native simple retrieval does not call the LLM. No additional documents can be written or uploaded through this API. To use approved, non-confidential data, create a validated JSONL file and set `AET_KNOWLEDGE_PATH` in local `.env`. Do not put client, personal or credential data in this prototype.

## Optional provider-native synthesis

After lexical retrieval, supported provider modes call the corresponding native LlamaIndex `LLM.complete()` integration. This does not turn the service into an agent. Models may hallucinate or fail to cite correctly; source IDs indicate retrieved passages, **not validated answer citations**.

| AET_PROVIDER | Optional package | Required model/deployment settings | Credential discovery |
| --- | --- | --- | --- |
| `ollama` | `.[ollama]` | `AET_OLLAMA_MODEL`, local `AET_OLLAMA_BASE_URL` | Local loopback HTTP |
| `openai` | `.[openai]` | `AET_OPENAI_MODEL` | `OPENAI_API_KEY` |
| `azure-openai` | `.[azure-openai]` | `AET_AZURE_OPENAI_MODEL`, `AET_AZURE_OPENAI_DEPLOYMENT`, `AET_AZURE_OPENAI_ENDPOINT`, `AET_AZURE_OPENAI_API_VERSION` | Azure SDK environment/identity |
| `anthropic` | `.[anthropic]` | `AET_ANTHROPIC_MODEL` | `ANTHROPIC_API_KEY` |
| `bedrock` | `.[bedrock]` | `AET_BEDROCK_MODEL_ID`, optionally `AET_AWS_REGION` | AWS SDK credential chain |

For example, generate with `agentkit new my-index --template llamaindex-rag --provider openai`, install `pip install -e ".[dev,openai]"`, and configure an authorised model and credentials before inference. `agentkit new ... --provider ollama --model llama3.2:1b` uses the existing compatible scaffolder CLI option.

Cloud inference is **opt-in, potentially billable** and sends prompts and retrieved data to an external model provider. CI runs only local mock and mocked provider tests; no paid model calls are made. Native model SDKs handle credentials rather than the scaffold.

## Security, deployment and operational limits

This is not production ready: unauthenticated HTTP, no tenancy, ACLs, rate limits, prompt-injection guarantees, telemetry, egress policy, cost budgets or production vector database. Run the API on localhost only. Synthetic records demonstrate plumbing, not enterprise retrieval correctness.

The generated `app/foundation.py` writes a server-issued request ID and sanitised JSON request logs without prompts, answers, secret headers, unknown routes or client addresses. Failure responses are sanitised, and `.env` is gitignored. A generated GitHub Actions workflow exercises offline tests on Python 3.12; a non-root Docker reference is included for local development. `.aet-template.json` allows Project Doctor to check project structure and syntax without importing the project.
