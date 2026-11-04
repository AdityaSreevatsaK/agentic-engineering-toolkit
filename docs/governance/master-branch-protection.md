# Protect the default branch (repository owner action)

This public repository should require a pull request and passing CI before
changes enter `master`. The repository owner must configure this in GitHub
Settings. Version-controlled documentation alone **does not activate** GitHub
branch protection.

## One-command owner setup (recommended)

This GitHub integration can inspect rulesets but has no ruleset-write action.
The repository owner can enforce these rules using the official **GitHub CLI**
and their **own GitHub account**. No personal access token or secret is stored
in this repository. Run from the repository root:

~~~powershell
gh auth login
python -m scripts.configure_branch_ruleset
python -m scripts.configure_branch_ruleset --apply
python -m scripts.configure_branch_ruleset --verify
~~~

The first Python command is a **local plan-only dry run**. The explicit
`--apply` makes the write using your authenticated `gh` CLI and then
verifies the resulting active ruleset. Repeating `--apply` is read-only
when the same ruleset is correctly installed; it never overwrites an
existing incomplete ruleset. The final `--verify` is read-only.
You need repository administration write access, and your GitHub plan must
allow branch rulesets for this repository. If a request fails, check
`gh auth status`, then use the Settings instructions below.

**Do not run the write command from CI.** It is a one-time repository-owner
governance action, not a source-code setting. It requires zero approvals
for a solo maintainer but requires PRs, all five CI checks, branch currency,
conversation resolution, and prevents deletion and force pushes. The rule
is targeted only at the default branch, without bypass actors.

## Configure a branch ruleset manually

1. Open **Settings > Rules > Rulesets > New ruleset > New branch ruleset**.
2. Name it `Protect master: PR and four-platform CI plus quality`, set **Enforcement
   status: Active**, and target **Default branch** (`master`).
3. Enable **Require a pull request before merging**. Set **required approving
   reviews to 0** for the current solo-maintainer workflow. GitHub does not
   allow you to approve your own pull requests.
4. Enable **Require status checks to pass before merging**, and select these
   four existing GitHub Actions checks from the `ci` workflow:

   - `smoke (ubuntu-24.04, 3.11)`
   - `smoke (ubuntu-24.04, 3.12)`
   - `smoke (windows-2025, 3.11)`
   - `smoke (windows-2025, 3.12)`

   Also require the dedicated `quality (ruff, mypy, bandit)` check.
   Turn on **Require branches to be up to date before merging** so status checks
   run against the current target branch. Select all five, not only an umbrella
   workflow status. GitHub must have reported each check recently to select it.
5. Enable **Block force pushes**, **Restrict deletions**, and **Require
   conversation resolution before merging**, if available.
6. Leave bypass permissions empty and avoid administrator exceptions when
   possible, so the protections also apply to the repository owner.
7. Save/create the ruleset, then revisit its detail page and confirm its
   **Active** status and all five required checks (four matrix jobs and the quality job).

GitHub docs: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository

## Verification

In **Settings > Rules > Rulesets**, confirm the ruleset is enabled for
`master`. Open a PR with failing/pending checks and verify GitHub blocks
merging. Do not force a failing merge or push directly to `master`.

The five checks are enforced by a **repository settings rule**, not by
`.github/workflows/ci.yml`. The workflow alone does not prevent bypasses.

## Recovery

If an incorrect rule blocks legitimate development, correct the ruleset
settings rather than deleting version history. Requiring an approval from the
sole author can permanently block solo-maintained PRs, which is why this
baseline requires a PR and CI, but does not mandate independent review.
