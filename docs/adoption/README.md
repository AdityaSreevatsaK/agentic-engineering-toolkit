# M15 adoption-validation kit

**Status:** Materials and automatic structural preflight are ready. **Real independent trials: not yet conducted.** No developer-time savings, team adoption, or positive user feedback is claimed.

## For a reviewer

Follow the [independent RAG exercise](independent-trial.md), using a clean Windows/Linux environment and synthetic data. The full exercise tests generation, validation, installation, actual HTTP behaviour, and one meaningful corpus change. Start with the offline mock provider; live Ollama/Bedrock is out of scope.

Use [reviewer-notes-template.md](reviewer-notes-template.md) in an approved private location to capture outcomes, including failures and assistance. Do not commit participant records, employer/client material, internal code or real credentials.

## Automated preflight (does NOT count as human validation)

From the repo root, with the scaffolder installed:

```powershell
python -m pip install -e .
python scripts/adoption_preflight.py
```

This creates all three templates in a temporary folder and checks registry metadata, template manifest, local mock mode, static Project Doctor, licence files and generated CI. It cleans up temporary projects automatically, makes **no paid model calls**, and produces machine-labelled JSON. To save a new report outside the repository:

```powershell
python scripts/adoption_preflight.py --json-out C:\approved\m15-preflight.json
```

Existing output files are never overwritten. This checks **structure only**. CI additionally installs and tests generated applications; neither test confirms that an unfamiliar engineer can use the toolkit independently.

## For the owner

1. Obtain required authorisation before any organisational user trial.
2. Invite at least two unfamiliar, consenting engineers to follow the [trial](independent-trial.md) without coaching. *No invitations have been made as part of M15.*
3. Record all attempted trials, failures, interventions and critical blockers in an approved location using the blank form.
4. Fix genuine usability defects in separate small PRs, without changing the protocol after seeing outcomes.
5. If business productivity evidence is sought, separately execute the [controlled paired study](../benchmarks/study_protocol.md) and the [existing local-only analyser](../pilot/README.md). Do not treat machine timings as human savings.
6. Update the [evidence register](evidence-register.md) **only after** actual independent evidence exists.

Before inviting anyone, the repository owner should also activate `master` protection using the [governance guide](../governance/master-branch-protection.md). Branch protection is a separate repository-admin setting; this M15 material does not enable it.

## What's deliberately not included

No claimed pilot completion, participant data, recruitment, ROI percentage, fictitious feedback, hosted dashboards, provider evaluations or new agent templates. AEA remains a separate evaluation asset.
