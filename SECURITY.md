# Security policy

AET is a reference scaffolder, not a security-certified production platform. Generated demonstration endpoints are unauthenticated and must not be exposed to the public internet without appropriate application security controls.

## Reporting vulnerabilities

Please avoid disclosing exploitable vulnerabilities, credentials, tokens or sensitive data in public GitHub issues or pull requests. If GitHub's private vulnerability reporting is enabled for this repository, use its **Security** tab to submit a private report. Otherwise contact the repository maintainer through an existing private, authorised channel before publishing technical exploit details.

## Supported development

Security-related corrections should target the default `master` branch. Old generated application copies and historical feature branches are not maintained releases.

## Data handling

Never commit real secrets, client information, internal company assets or personal data. Tests use synthetic records or a restricted, publicly sourced evaluation subset. Actions logs and artifacts in public repositories are visible to others.
