# AET comprehensive supported-combination test report

**Date:** 4 November 2026  
**Scope:** Registry-declared template/provider combinations, Python 3.11 and 3.12, Windows 2025 and Ubuntu 24.04  
**Tested source commit:** 5bd2684bc9afad02e21a03d3f6b9e3a84b731afb  
**Evidence:** [GitHub Actions run 41781179570](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions/runs/41781179570) (completed successfully)  
**Verdict:** **PASS for the stated offline test scope; not evidence of live cloud-provider or production readiness.**

## 1. Executive summary

The sweep exercised **every valid framework-template / provider pairing declared in the AET registry** on each of four CI environments. It tested **23 supported pairings per environment**, or **92 generated-project executions**, plus **29 rejected/invalid cases per environment**, or **116 negative checks**. The new matrix and all existing CI steps passed.

| Environment | Supported pairs passed | Negative checks passed | Full CI job |
| --- | ---: | ---: | --- |
| Ubuntu 24.04, Python 3.11 | 23/23 | 29/29 | PASS |
| Ubuntu 24.04, Python 3.12 | 23/23 | 29/29 | PASS |
| Windows 2025, Python 3.11 | 23/23 | 29/29 | PASS |
| Windows 2025, Python 3.12 | 23/23 | 29/29 | PASS |
| **Total** | **92/92** | **116/116** | **4/4 smoke jobs passed** |

The independent **quality (Ruff, focused mypy, Bandit)** job passed, making **5/5 required jobs successful**. These are observed results from the run above, not estimates.

No new defect was reproduced by this test scope. This is **not** a claim that no defects exist elsewhere.

## 2. Complete declared provider matrix

| Template | Mock | Ollama | OpenAI | Azure OpenAI | Anthropic | AWS Bedrock | Pair count |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | ---: |
| tool-agent (LangGraph deterministic tools) | Yes | Yes | Yes | Yes | Yes | Yes | 6 |
| langgraph-rag | Yes | Yes | Yes | Yes | Yes | Yes | 6 |
| strands-agent | Yes | **Unsupported** | Yes | Yes | Yes | Yes | 5 |
| llamaindex-rag | Yes | Yes | Yes | Yes | Yes | Yes | 6 |
| **Declared combinations** | | | | | | | **23** |

Here, **Yes means generated, structurally verified, and executed using a forced offline mock runtime**. It **does not** mean the named provider was contacted successfully. Strands/Ollama is an intentional unsupported combination; the negative test verifies it is rejected.

## 3. What every one of the 92 valid cases checked

1. Generated a new, isolated project from the specified template/provider combination, including a nondefault syntactically valid Ollama model when applicable.
2. Passed **agentkit Doctor** for required files, manifest, metadata, sample settings and all generated Python syntax. Doctor does not import dependencies or contact a provider.
3. Verified the template manifest identity and that the sample environment configuration selects the requested provider, with no raw API-key or AWS secret assignments.
4. Confirmed that generating into the same target path again is refused (no overwrite).
5. Ran a **real FastAPI TestClient request in a separate Python interpreter**, forcing **AET_PROVIDER=mock** using a restricted child environment. This avoids paid model invocation even for cloud-selected scaffolds.
6. Required GET /health and GET /ready to succeed, a synthetic /invoke tool request or /ask retrieval request to succeed, and an empty question to return HTTP 422.
7. For both RAG templates, appended a synthetic reference passage to the isolated corpus and required a subsequent query to retrieve the new source and its expected content.

This is more than generation-only validation: it exercised HTTP routes, tools/retrieval, validation and RAG corpus updates in all 92 generated instances, **but only in mock mode**.

## 4. Negative tests

Each of the four environments additionally passed:

| Negative category | Checks per environment |
| --- | ---: |
| Explicitly unsupported Strands/Ollama pairing | 1 |
| Unknown provider rejected by every template | 4 |
| Unsafe directory/project name rejected by every template | 4 |
| Ollama-only model CLI argument rejected for every other supported provider | 20 |
| **Total** | **29** |

The no-overwrite check was additionally executed for **each of the 23 valid pairs** and counted in the positive-case contract, not duplicated in the negative total.

## 5. Other tests in the same successful workflow

The CI workflow also ran the pre-existing scaffolder/Doctor unit suite; generated-app tests for all four frameworks, including SDK-constructor tests using **injected offline cloud-provider doubles**; Ollama mocked-HTTP tests; Strands SDK offline tool-loop and fake Bedrock wiring tests; portable-provider and Agent Quality Kit unit/packaging checks; synthetic dataset evaluations; actual generated-app API smoke tests; installable-wheel checks; and a **tool-agent Docker build on Ubuntu/Python 3.11**. Static quality checks covered Ruff error/unused-symbol rules, focused mypy checks and high-severity Bandit checks.

**Important distinction:** The entire provider grid runs mock inference. SDK integration code paths are additionally tested by *separate unit suites using fakes*. A successful fake SDK test does not demonstrate live OpenAI, Azure OpenAI, Anthropic or Bedrock account connectivity.

## 6. Evidence and reproduction

- [Exact CI execution and step logs](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions/runs/41781179570)
- The CI run contains four uploaded **comprehensive-matrix-<OS>-py<version>** JSON artifacts, with per-pair results, negative-case results and explicitly recorded scope limitations. Artifacts are retained for **30 days**.
- Source of the reproducible matrix: [scripts/comprehensive_matrix.py](../../scripts/comprehensive_matrix.py)
- Root contract tests: [tests/test_comprehensive_matrix.py](../../tests/test_comprehensive_matrix.py)
- Existing isolated HTTP probe reused by the matrix: [scripts/release_smoke.py](../../scripts/release_smoke.py)

To reproduce locally after cloning the repository, install Python 3.11 or 3.12 and use a fresh environment. The matrix requires generated-app dependencies to be available; the full GitHub workflow installs them before the sweep. Example in PowerShell:

~~~powershell
python -m pip install -e . pytest
foreach ($template in @("tool-agent", "langgraph-rag", "strands-agent", "llamaindex-rag")) {
    python -m aet_scaffolder new "deps-$template" --template $template --provider mock
    Push-Location "deps-$template"
    python -m pip install -e ".[dev]"
    Pop-Location
}
python -m scripts.comprehensive_matrix --json-out local-comprehensive-matrix.json
~~~

Run in a disposable checkout/directory to avoid retaining generated projects. Use a new report filename on each rerun because the script intentionally refuses to overwrite evidence.

## 7. Explicit limitations and remaining validation

**Not tested or proven by this report:**

- Actual billable inference or authentication against OpenAI, Azure OpenAI, Anthropic or AWS Bedrock; model/region permissions, latency and tool-support compatibility remain unverified.
- A real running Ollama daemon or locally downloaded model. Ollama transport is exercised using mocks elsewhere in the same CI.
- Installing provider-specific optional SDK extras separately for *every* generated project; the matrix uses the dependencies installed earlier in the runner.
- All possible Python versions, operating systems, dependency releases, model IDs, environment-variable values, concurrent workloads or hostile client inputs. The tested set is **exhaustive only for the declared 23 template/provider pairs across the four stated CI environments**.
- All Docker images: only the tool-agent reference image was built in this run.
- Production identity, tenant isolation, rate limiting, operational controls, live cloud correctness, security penetration testing, licensing/IP authorisation, independent human usability, developer productivity gains or adoption by multiple teams.

**Recommended before a production suitability claim:** approved live-provider integration tests, a reviewed security/operations design, reproducible dependency locks, an independent clean-laptop onboarding trial and measured time-to-first-working-agent against a manual baseline. Enable GitHub ruleset protection for master (repository owner action).

## 8. Conclusion

**PASS: Comprehensive offline scaffold correctness and synthetic runtime checks for all declared template/provider combinations on Windows and Linux, Python 3.11 and 3.12.**

This is credible **controlled-pilot and leadership-demo** evidence. Describe cloud integrations as **provider adapters with offline SDK-double validation, pending approved live verification**, not as fully verified production connections.
