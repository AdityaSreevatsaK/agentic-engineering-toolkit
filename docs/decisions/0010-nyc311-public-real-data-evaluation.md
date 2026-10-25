# ADR-0010: Permission-aware public NYC 311 evaluation

Status: Accepted for M10 reference implementation.

The original Olist public dataset used in M9 has a CC BY-NC-SA 4.0 license, requiring caution for employer-facing use. NYC Open Data explicitly says its open datasets can be used without usage restrictions, subject to the city's terms and any data-specific notices.

Implement a bounded, attributable 311 status query (`unique_key,status`) and run an actual *temporary* generated FastAPI/LangGraph application with independent Quality Kit traces. Use real official rows only in one designated CI job, capture an aggregate-only result, and run separate synthetic fixtures across all CI platforms.

Do not commit original city records, exact request IDs or private caller data to the repo. Never claim the deterministic in-memory lookup benchmark measures real LLM performance, public 311 service availability, business deployment latency, team adoption or human productivity improvements.

Network availability, source freshness and updates remain external risks. The CI must not substitute synthetic data on official-source failures.
