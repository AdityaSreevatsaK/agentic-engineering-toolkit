# ADR-0017: Strands native cloud provider flexibility

Status: Implemented in M17; acceptance requires four successful OS/Python smoke jobs.

## Context

The `strands-agent` scaffold has a true Strands SDK tool loop, but previously offered only a deterministic offline Model and Amazon Bedrock. Teams evaluating the template for projects using OpenAI, Azure OpenAI or Anthropic could not select their authorised enterprise provider without rewriting the bootstrap.

## Decision

- Preserve the existing `mock` offline model, existing `BedrockModel` configuration and `Agent` construction unchanged.
- Add native `strands.models.openai.OpenAIModel` and `strands.models.anthropic.AnthropicModel` providers.
- For Azure, use the official `openai.AsyncAzureOpenAI` SDK client injected into the native Strands `OpenAIModel`; this is compatible with Strands' documented custom-client entry point.
- Read model, deployment, endpoint and API version via `AET_*` environment-based `Settings`. Let provider SDKs resolve credentials from established environment or identity sources. Do not check in tokens, profiles or keys.
- Install optional cloud SDK dependencies only through `.[openai]`, `.[azure-openai]`, `.[anthropic]` or `.[cloud]`. Core mock/Bedrock scaffolding remains unchanged.
- Reject malformed Azure endpoint URLs, missing model/deployment settings and invalid provider selections. HTTP errors remain sanitised.
- Keep original Project Doctor structural requirements stable so existing M13/M14 Strands generated projects remain valid. New generation still includes `app/cloud_models.py`.
- CI tests inject fake native SDK implementations. No cloud accounts, model downloads or paid API calls.

## Consequences and limitations

Provider flexibility is not production readiness. The generated FastAPI service lacks authentication, multi-tenancy, tool authorisation, rate limits and egress isolation. Native cloud SDKs may require separately approved deployments and billing. Provider-level streaming, model tool use, token budgets and real credential health remain unverified until a suitably authorised team runs optional, separate integration checks.

M16 has already added cloud provider choices to both LangGraph templates. M17 integrates against that baseline, preserving all LangGraph options, generated-app CI and historical Project Doctor compatibility.
