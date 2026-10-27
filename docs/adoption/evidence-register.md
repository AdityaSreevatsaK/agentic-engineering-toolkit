# M15 evidence register: do not conflate categories

**Snapshot: 27 October 2026**
**Status: CI-backed preflight available, author-operated smoke test reported, external human validation uncollected.**

| Evidence category | Current status | Valid supporting evidence | What it does NOT show |
| --- | --- | --- | --- |
| AET engineering implementation | Verified via merged M11–M14 PRs and four-platform CI | PRs #11, #12, #14, #15, successful GitHub Actions for master | Adoption, productivity savings or model quality |
| Licence and distribution | Apache-2.0 grant merged via PR #16 | Root/package/generated LICENSE and NOTICE files; CI validation | Security certification or employer endorsement |
| Automated M15 structural preflight | Script and repeatable CI test added; actual CI result depends on run | `scripts/adoption_preflight.py` output labelled `automated_structural_preflight` | Human task completion, actual HTTP operation or saved time |
| Author-operated RAG smoke test (27 October 2026) | **Self-reported successful with two documentation gaps** | Private screenshots show 29 passed, 1 skipped in 3.30s; Uvicorn starting/stopping/restarting; and two POST /ask requests returning HTTP 200. The author reports the exercise worked and requested fuller file paths and stop/start instructions. | Independent reviewer usability; exact API response contents/source IDs (not visible in screenshots); cause of skipped test; productivity savings |
| Independent fresh-user execution | **Not collected (optional when reviewers become available)** | Reproducible checklist, tests and authorised observations from an unfamiliar engineer | Statistical ROI or multi-team adoption |
| Multi-team reuse | **Not established** | Separate authorised adopter/project/team confirmations and provenance | Inferred adoption from GitHub views/stars |
| Matched developer-time savings | **Not measured** | Counterbalanced manual-vs-toolkit trials and [existing analyser](../pilot/README.md) | Savings inferred from fast code generation alone |
| Live LLM/provider correctness | **Not verified** | Separate approved integration and quality studies | Demonstrated by mock-mode CI |

## Promotion-friendly statement, supported today

"Designed and released a publicly accessible Apache-2.0-licensed agent project scaffolder with three runnable Python templates, template-aware validation, isolated mock providers, generated CI, non-root Docker examples, and Windows/Linux Python 3.11/3.12 automated tests. Established a documented protocol for independent adoption trials and honest impact measurement."

**Additional supported note:** The author exercised the local generated RAG service and identified missing instructions for the file's absolute path and Uvicorn restart. The resulting documentation amendment is **not** independent validation. Private screenshots containing device details are not published in this repository.

**Do not add:** "adopted across teams", "reduced setup by N%", "production deployed", "AWS Bedrock integration validated live", or "engineers validated independently" until independently evidenced.

## Pending gates

- Repo owner must activate GitHub ruleset for `master`. [Issue #13](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/issues/13) remains open.
- Obtain any needed permission for real reviewer trials.
- Independent fresh-user trials are **optional if reviewers become available**; do not make lack of volunteers an engineering milestone blocker.
- If beneficial, complete matched productivity trials with balanced order before making improvement claims.

Existing [historical M8 KRA evidence](../pilot/kra_evidence_register.md) remains intact for provenance; it predates AET's public licensing and its newer scaffolder-only scope.
