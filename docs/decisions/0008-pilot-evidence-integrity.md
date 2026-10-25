# ADR-0008: Pilot impact evidence without fabricated adoption

Status: Accepted for M8 pilot-preparation tooling.

## Context

The toolkit has seven merged implementation milestones and CI-verified demo behavior. Neither CI run time nor documentation demonstrates that working engineers save time or have adopted the assets.

## Decision

Implement a local-only standard-library CSV analyzer for prospective paired manual-versus-toolkit trials. Use exact input schema, reject malformed or contradictory records, compare only matched completed trials that passed acceptance checks, count failures and unpaired participants separately, and return anonymized aggregate values only.

An empty template returns `no_data`. A pilot status threshold (at least five completed matched pairs and both trial orders represented) means **ready for human review**, not proof of causality, organizational adoption or production performance. Avoid committing real participant data.

Document approval, private-repo IP/ownership review, independent usability review and evidence boundaries. Keep CI fixtures synthetic.

## Consequences

Automated test results remain engineering evidence only. The analyzer cannot validate consent, true independence, comparable machines, adherence to timing methods or statistical significance. These must be reviewed by humans before any productivity or adoption claims.
