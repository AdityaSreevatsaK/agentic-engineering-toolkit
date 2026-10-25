# ADR-0004: Read-only generated-project verification

Status: Accepted for M3 prototype

## Context

A reusable CLI must give developers immediate feedback after project generation, including when Python application dependencies are absent. Shipping from an editable source checkout does not prove that packaged wheels contain the bundled template files.

## Decision

Add `agentkit doctor` using only the Python standard library. The doctor verifies expected files, parses TOML metadata, verifies sample provider settings, and uses Python `compile` to parse source **without executing it**. JSON output and machine-readable exit status support automated checks.

Add a GitHub Actions wheel-distribution smoke test on both Windows/Linux. CI installs the generated package from the built wheel and confirms that template resources remain available.

## Limitations

Doctor reports structural/static integrity only; it does not prove functional correctness, secure deployment, network isolation, or performance. The repository still ships only one project template and two response-provider configurations. Real local Ollama tests require a separate opt-in demonstration.
