# M15 adoption-validation kit

**Status:** Materials and structural preflight are ready. The author reported a successful local RAG smoke test on 27 October 2026. **No independent reviewer trials, team adoption or developer-time savings have been measured.** See the [evidence register](evidence-register.md).

## Updated M19 acceptance and leadership kit

The [M19 release-readiness kit](../release/README.md) provides an automated
four-template mock HTTP smoke and synthetic corpus-change test, a separate
unfamiliar-engineer walkthrough, evidence gate checklist and leadership
architecture review. Running the automated smoke is **not** an independent
human trial or proof of developer productivity.

## For a reviewer

Follow the [independent RAG exercise](independent-trial.md), using a clean Windows/Linux environment and synthetic data. The full exercise tests generation, validation, installation, actual HTTP behaviour, and one meaningful corpus change. Start with the offline mock provider; live Ollama/Bedrock is out of scope.

Use [reviewer-notes-template.md](reviewer-notes-template.md) in an approved private location to capture outcomes, including failures and assistance. Do not commit participant records, employer/client material, internal code or real credentials.

## Automated preflight (does NOT count as human validation)

From the repo root, with the scaffolder installed:

```powershell
python -m pip install -e .
python scripts/adoption_preflight.py
```

This creates all four registered templates in a temporary folder and checks registry metadata, template manifest, local mock mode, static Project Doctor, licence files and generated CI. It cleans up temporary projects automatically, makes **no paid model calls**, and produces machine-labelled JSON. To save a new report outside the repository:

```powershell
python scripts/adoption_preflight.py --json-out C:\approved\m15-preflight.json
```

Existing output files are never overwritten. This checks **structure only**. CI additionally installs and tests generated applications; neither test confirms that an unfamiliar engineer can use the toolkit independently.

## For the owner

1. Obtain required authorisation before any organisational user trial.
2. If independent reviewers become available, invite consenting engineers to follow the [trial](independent-trial.md). **Finding two reviewers is an optional evidence goal, not a blocker for AET engineering progress.** No independent results have been recorded.
3. Record all attempted trials, failures, interventions and critical blockers in an approved location using the blank form.
4. Fix genuine usability defects in separate small PRs, without changing the protocol after seeing outcomes.
5. If business productivity evidence is sought, separately execute the [controlled paired study](../benchmarks/study_protocol.md) and the [existing local-only analyser](../pilot/README.md). Do not treat machine timings as human savings.
6. Keep the [evidence register](evidence-register.md) accurate: an author-operated test can show functionality and documentation friction, but does not substitute for an independent trial.

Before inviting anyone, the repository owner should also activate `master` protection using the [governance guide](../governance/master-branch-protection.md). Branch protection is a separate repository-admin setting; this M15 material does not enable it.

## What's deliberately not included

No claimed independent pilot completion, participant data, recruitment, ROI percentage, fictitious feedback, hosted dashboards, provider evaluations or new agent templates.
