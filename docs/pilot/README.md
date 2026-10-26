# M8 — Engineering pilot and impact validation

> Historical M8 protocol. The repository is now **public** and Apache-2.0 licensed; statements below about private-only access describe its earlier state. For the current three-template scaffolder, begin with the [M15 hand-off kit](../adoption/README.md). No independent human validation has been performed.

**State: pilot-ready materials, NOT a conducted pilot.** All participant and productivity evidence fields remain blank unless an independent, approved reviewer actually supplies observations. The repository is private; do not upload employer/client content or identifiable reviewer records.

## Phase 0 — Authorization before invitations

Obtain confirmation from the appropriate employer/project owner that a pilot using this **personal private GitHub repository** is permitted, including ownership/IP treatment, who can view the code and results, and any restrictions on AI coding tools or external services. If approval is not granted, do not share repository access or run trials on company systems. The default demo uses only synthetic data and mock providers; no real client credentials or datasets are needed.

## Phase 1 — Independent reproducibility review (qualitative)

Invite 2–3 permitted engineers to follow [M7 demo instructions](../demo/README.md) independently (a suggested target, **not** participants already recruited). They should reproduce the offline demo, try `agentkit new` / `agentkit doctor`, evaluate the Quality Kit and Provider Contract examples, and use the [reviewer checklist](../demo/reviewer-checklist.md).

Use the existing **blank** [review notes template](../demo/review-notes-template.csv) to record pseudonymized, consented feedback in an approved location. Do not equate these reviews with the controlled productivity study.

## Phase 2 — Paired developer productivity trials (quantitative)

Follow the precommitted [trial protocol](../benchmarks/study_protocol.md). Each consenting participant performs the same acceptance-tested task in two conditions: manual and toolkit, counterbalanced across trial order, using approved Python/environment/AI assistance. Report failures and incompletes separately instead of excluding them from completion-rate calculations.

Collect data with [trials-template.csv](trials-template.csv), using **synthetic-looking pseudonymous codes only** and *no personal details*. Keep real trial CSV files in an employer-approved location; the CLI below runs locally without network requests.

The protocol suggests **at least five independent pairs** for a pilot. A smaller sample is exploratory, and even larger observational results are not proof of causality.

### Local-only analysis

Use Python 3.11+ from the repository root:

```powershell
python scripts/analyze_pilot.py --input docs/pilot/trials-template.csv
```

An untouched blank template prints `"status": "no_data"` and no performance claim. For properly collected, approved trial data:

```powershell
python scripts/analyze_pilot.py --input C:\approved\pilot-trials.csv --json-out C:\approved\pilot-aggregate.json
```

The script accepts exactly these columns:

| Column | Allowed values / rule |
|---|---|
| `participant_code` | Anonymous code with letters, digits, underscores or dashes; not a real name/email |
| `condition` | `manual` or `toolkit` |
| `trial_order` | `1` or `2` (each matched person must use both) |
| `active_minutes` | Finite number above 0 and no more than the predeclared 120-minute cap |
| `completed`, `tests_passed` | `yes` or `no` |
| `os` | `Windows`, `Linux` or `macOS` |
| `python_version` | `3.11` or `3.12` |

A *successful comparable pair* needs both trials to be completed with passing tests. Incomplete trials contribute to completion rates, not the successful-pair timing denominator. The analyzer reports trial counts, both condition completion rates, paired medians and a relative median difference only when such pairs exist. It cannot verify participant independence, real consent, equivalent hardware/assistance, or confounding factors. Those require manual review.

Do not commit real pilot CSV files or reports to this personal repository. The GitHub CI only exercises entirely synthetic fixtures and the **empty template**.

## Phase 3 — KRA evidence package

Use [KRA evidence register](kra_evidence_register.md) to separate: (a) independently verified software results, (b) proposed architecture, (c) uncompleted real-world validation, and (d) future evidence. Update with approved pilot findings only after they exist. Always mention samples, completion rates, study limitations, and who conducted the review.

## Suggested go/no-go gates

A broader pilot is conditional on approval, independent demo reproducibility, a clear code/IP owner, absence of sensitive input, a responsible maintainer, and no critical blockers reported by reviewers. Live Ollama or cloud service tests are **not** required for this offline pilot, and none should be introduced without separate authorization.
