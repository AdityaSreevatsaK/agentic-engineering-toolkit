# M10 verified public NYC 311 status evaluation — 25 October 2026

## Provenance and reproducibility

- Official dataset: [NYC Open Data, 311 Service Requests from 2020 to Present](https://data.cityofnewyork.us/d/erm2-nwe9), identifier `erm2-nwe9`.
- Data owner / attribution: City of New York, NYC 311 / Office of Technology and Innovation.
- Recorded retrieval: **2026-10-25 09:11:20 UTC**.
- Source query: `$select=unique_key,status&$order=unique_key DESC&$limit=120` through the official `/resource/erm2-nwe9.json` endpoint. This is a **bounded ordered slice, not a statistically random sample**.
- GitHub CI run: [Run #40179566646](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions/runs/40179566646), Ubuntu Python 3.11 job. The `m10-nyc311-official-py3.11` artifact contains only aggregate JSON (artifact retention 14 days).
- Record snapshot SHA-256 fingerprint (sorted public request-ID/status pairs): `8b3290cbf1fc059c56d24cd9f4f19ac0bea851c4094fb3257a0cb88c9be769e3`. IDs are **not** published here.

## Observed results

| Metric | Observed |
|---|---:|
| Official records retrieved | 120 |
| Status Closed | 43 |
| Status In Progress | 77 |
| Generated-project static checks | 16 passed |
| Known service request statuses correctly returned | 100 of 100 |
| Known status lookup exact-match accuracy on tested slice | 100.0% |
| Unknown request ID check | 1 of 1 passed |
| Malformed request skips status lookup tool | Passed |
| Median in-process request latency | 2.255 ms |
| Nearest-rank p95 latency | 2.524 ms |
| Maximum request latency | 10.225 ms |

The evaluation generated a fresh mock agent and patched only the *temporary test graph* to interpret 311 numeric request identifiers, then checked FastAPI responses, LangGraph routing and independent Quality Kit tool assertions against the retrieved statuses.

## Claim boundaries

These are **genuine measurements made with actual government-published records**, not a fabricated or Olist-shaped CSV. They validate deterministic dictionary lookup and software integration **only**. There was **no LLM call** in this test; no evaluation of natural-language semantic reasoning, real municipal service backend, throughput, production network, live data freshness, or developer productivity was performed.

The 100% figure is accuracy on the 100 deterministic lookups tested and must **not** be represented as full-dataset accuracy, open-domain agent accuracy or production SLA. The 120 record source slice is order-based and reflects the source at one instant. The original Olist dataset was **not** used.

Use [NYC Open Data FAQ](https://www.nyc.gov/opendata/get-started/FAQs) and [Terms](https://data.cityofnewyork.us/stories/s/Terms-of-Use/k9k7-3cje) when documenting permitted reuse and required attribution. Employer internal IP and usage policies still apply.
