# Protect the default branch (repository owner action)

This public repository should require a pull request and passing CI before
changes enter `master`. The repository owner must configure this in GitHub
Settings. Version-controlled documentation alone **does not activate** GitHub
branch protection.

## Configure a branch ruleset

1. Open **Settings > Rules > Rulesets > New ruleset > New branch ruleset**.
2. Name it `Protect master: PR and four-platform CI`, set **Enforcement
   status: Active**, and target **Default branch** (`master`).
3. Enable **Require a pull request before merging**. Set **required approving
   reviews to 0** for the current solo-maintainer workflow. GitHub does not
   allow you to approve your own pull requests.
4. Enable **Require status checks to pass before merging**, and select these
   four existing GitHub Actions checks from the `ci` workflow:

   - `smoke (ubuntu-latest, 3.11)`
   - `smoke (ubuntu-latest, 3.12)`
   - `smoke (windows-latest, 3.11)`
   - `smoke (windows-latest, 3.12)`

   Turn on **Require branches to be up to date before merging** so status checks
   run against the current target branch. Select all four, not only an umbrella
   workflow status. GitHub must have reported each check recently to select it.
5. Enable **Block force pushes**, **Restrict deletions**, and **Require
   conversation resolution before merging**, if available.
6. Leave bypass permissions empty and avoid administrator exceptions when
   possible, so the protections also apply to the repository owner.
7. Save/create the ruleset, then revisit its detail page and confirm its
   **Active** status and all four required checks.

GitHub docs: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository

## Verification

In **Settings > Rules > Rulesets**, confirm the ruleset is enabled for
`master`. Open a PR with failing/pending checks and verify GitHub blocks
merging. Do not force a failing merge or push directly to `master`.

The four checks are enforced by a **repository settings rule**, not by
`.github/workflows/ci.yml`. The workflow alone does not prevent bypasses.

## Recovery

If an incorrect rule blocks legitimate development, correct the ruleset
settings rather than deleting version history. Requiring an approval from the
sole author can permanently block solo-maintained PRs, which is why this
baseline requires a PR and CI, but does not mandate independent review.
