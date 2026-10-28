# M19 evidence and release gate

The goal is **pilot-readiness**, not declaring production readiness or
claiming developer-time savings. Complete/check each gate only with evidence
from its actual execution; this file contains no fabricated outcomes.

| Gate | Acceptance requirement | Evidence | State in repository |
| --- | --- | --- | --- |
| Code and packaging | Four templates in one installable AET wheel; old generated projects remain valid | Unit tests, Doctor, package tests | Automated test coverage available |
| Functional smoke | Four generated mock apps pass health/readiness, request handling and invalid-input checks; both RAG variants reflect corpus change | `scripts/release_smoke.py` per-platform JSON | CI must be checked on final M19 SHA |
| Compatibility | All four Windows/Linux Python 3.11/3.12 jobs successful on final integrated commit | GitHub Actions matrix | CI must be checked on final M19 SHA |
| Independent usability | At least one authorised non-author engineer independently performs the primary two-request corpus trial | Private completed observer notes | **Not collected** |
| Developer-time improvement | Balanced manual-vs-AET matched baseline with explicit active/wait time | [M4 protocol](../benchmarks/study_protocol.md) | **Not measured** |
| Multi-team adoption | Independent confirmed use by more than one authorised delivery team | Approved adopter/project evidence | **Not verified** |
| Production suitability | Security, identity/ACL, operational controls, cloud provider validation | Client-specific architecture review and tests | **Out of scope / not verified** |
| Governance | PR/CI ruleset active for `master` | [Owner setup steps](../governance/master-branch-protection.md) | **Owner action required; not verified** |

A passing pipeline permits describing AET as a **CI-verified local-first
scaffolder and controlled pilot candidate**. It does not satisfy the remaining
human adoption, productivity, security, governance or employer-approval gates.
Completed reviewer notes must remain outside this public repository.

**Minimum next action for the owner:** Confirm organisation/IP permission and
the GitHub ruleset. Offer the synthetic-data reviewer protocol to an
authorised unfamiliar engineer when available. Record only real outcomes.
