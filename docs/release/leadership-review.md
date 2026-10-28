# AET: architecture and reusable-asset leadership review (M19)

**Decision requested:** Approve AET as a candidate for a *controlled, synthetic
data pilot* and identify one authorised delivery-team contact. This is not
a request for public production deployment or a claim of proven ROI.

## Engineering problem and design decision

Teams building agentic Python services repeatedly need project layout,
framework setup, model/provider configuration, offline testing, API health
and basic operational scaffolding. AET standardises these foundations
with reproducible, self-contained starter projects, rather than imposing
a single proprietary runtime.

| Concern | AET architecture | Proof available |
| --- | --- | --- |
| Developer entry point | `agentkit list/new/doctor`; manifest-bound template registry | CLI and validation tests |
| Application isolation | Four independent Python project templates, no shared runtime required | Generated tests and wheel contents |
| Framework selection | LangGraph tool routing / BM25 RAG, Strands SDK tool agent, native LlamaIndex keyword RAG | Real offline workflow and SDK tests |
| Provider selection | Mock; configurable OpenAI/Azure OpenAI/Anthropic/Bedrock; Ollama where supported | SDK-constructor fakes and configuration tests; **not** live provider acceptance |
| API foundations | Local FastAPI endpoints, sanitised request logs, request IDs, offline readiness, dev Docker | Four-platform CI and non-root build smoke |
| Adoption mechanics | Documented quickstart and corpus-change exercise, machine-only reproducibility probe | Automated local checks; **no independent user validation yet** |

## Reference execution flow

`CLI -> template registry -> atomic project generator -> independent app
(project configuration -> framework runtime -> optional provider SDK) ->
local FastAPI -> tests/Doctor/CI`.

For RAG templates: `synthetic JSONL corpus -> local lexical index/retriever ->
source IDs -> mock evidence response OR optional model synthesis`.
For Strands: `synthetic request -> Strands SDK Agent -> read-only tool ->
scripted offline/model-generated response`. The tool-agent's order routing
is deterministic, not autonomous planning.

## Verifiable outcomes versus assumptions

| Outcome | Status | Evidence boundary |
| --- | --- | --- |
| Four templates committed and runnable in mock mode | Implemented | M12/M13/M16–M18 PRs, tests and generated-app CI |
| Windows and Linux / Python 3.11 and 3.12 automated coverage | Verified | GitHub Actions checks for the final merge |
| Isolated-workspace HTTP and synthetic corpus-change reproducibility | M19 automation | CI after this PR merges; uses preinstalled generated-app dependencies |
| Setup-time reduction versus manual baseline | **Not measured** | Needs paired human trial and independent work-time records |
| Multiple delivery teams adopting AET | **Not verified** | Requires authorised project/team confirmations |
| Security for enterprise production deployment | **Not achieved** | AuthN, AuthZ, tenant isolation, policy, budget and observability missing |

## Risks and adoption boundary

- Unauthenticated generated APIs must stay on loopback until properly hardened.
- Provider credentials, cloud authorisation, model availability and billable
  inference are not verified by mock-only CI.
- Retrieval is lexical (BM25 / keyword); semantic retrieval, document ACLs,
  tenancy and persistence are not part of this reference.
- Existing templates are deliberately simple, with bounded synthetic data.
- Public repository use by an employer/client requires explicit IP, licence
  and security approval; no client data should be uploaded or committed.

## Proposed low-friction next decision

1. Review the architecture and acceptance checklist with one authorised
   engineering architect/lead. Record **actual** approval or changes needed.
2. Give an unfamiliar consenting engineer the fresh-user walkthrough,
   collect private observations and fix measured friction.
3. If needed, run the separate counterbalanced manual-vs-AET study for
   defensible time claims, then request multi-team pilot adoption.
4. Keep AET feature-frozen except defects or observed adopter needs.

**Presentation summary:** Cross-framework and cross-provider scaffolding
with a unified developer-facing contract; reproducible offline prototypes
and CI evidence; security and measured adoption remain explicit gates.
