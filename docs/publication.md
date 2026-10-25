# Public repository publication notes

AET was initially developed and documented as a private engineering prototype. Its repository was subsequently made public. Old milestone decisions, PR conversations and evidence referencing private access are retained as *historical statements*, not the present visibility policy.

## Publication boundaries

- The maintainer has explicitly released the AET source and three installable Python distributions under **Apache License 2.0**. The root and standalone package LICENSE and NOTICE files describe the rights and attribution obligations. Newly generated projects also contain those files. External dependencies retain their own licences. Apache 2.0 allows commercial reuse and modification; it does not require future users to contribute their changes back.
- All synthetic datasets and the official NYC 311 public-data integration are disclosed with scope limitations. No employer/team adoption or measured developer time savings are claimed.
- Public Actions logs and uploaded artifacts are visible to others; only synthetic data, sanitised aggregates and mock provider responses belong in automated runs.
- No credentials or client-owned materials should be committed.
- Earlier private-only instructions in historical ADRs and PRs were appropriate at the time and are deliberately preserved as provenance.

## Current product boundary

Only the **Agent Project Scaffolder** is an active AET product. The old Quality Kit, Provider Contract, pilots, benchmarking and evaluation scripts remain available for reproducibility and backwards compatibility. AEA is a separate evaluation product.

## Public development workflow

Changes use a feature branch and PR, the existing Windows/Linux Python 3.11/3.12 matrix must pass on the exact head, and then approved changes can be merged. The repository owner must configure `master` protection in GitHub Settings, as specified in [the branch protection guide](governance/master-branch-protection.md). Repository CI alone cannot prevent merging failing changes.
