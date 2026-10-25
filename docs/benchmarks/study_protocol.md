# M4 developer productivity study — preregistered protocol

**Status:** Prepared, not yet run. No manual baseline or percentage improvement is claimed.

## Separate what we measure

1. **Automated microbenchmark:** `agentkit-benchmark` reports Python file-generation and static-validator timings. It does **not** include dependency installation, API start, actual local model inference, writing code, or developer time. This is useful for regression tracking, not proof of productivity.
2. **Developer trial:** compare elapsed *active human time* to reach the same acceptance criteria using an empty project directory versus the AET scaffolder. This is the source of any eventual developer-time-saving claim.

## Controlled trial task

Build a working local Python application with:
- FastAPI `GET /health` and `POST /invoke`, request validation, response containing `answer` and optional `tool_used`.
- A LangGraph workflow; deterministic routing to a synthetic order-status tool when the exact order-status command is provided.
- A mock text provider as default, plus a replaceable local Ollama text-generation adapter whose networking can be stubbed.
- Documented environment variables with no credentials, a README for native Windows, and an executable pytest suite.
- Passing tests for basic health, mock response, known and unknown synthetic orders, invalid input, and locally mocked provider behavior.

Stop the timer only when the project installs (with pre-approved dependencies), all tests pass, and both HTTP endpoints pass a brief manual check.

## Conditions

- **Manual (A):** start in an empty directory, use ordinary Python tools and documentation. Do not copy generated AET files or invoke any project scaffolding generator.
- **AET (B):** start in an empty directory, generate with `agentkit new ...`, verify with `agentkit doctor`, then install, run and fix issues if needed.
- Same workstation class, network, Python version, base package index, IDE, and approved AI assistance in both conditions. Record deviations.
- Preinstall Python and the AET CLI and prepare access to dependencies **before both timers**. Treat these as one-time prerequisites, and report separately if needed.
- Begin timing at first project-specific work; include edits, failing tests, troubleshooting and retrying.
- Balance trial order A/B then B/A across participants to reduce learning bias. Use fresh project names and no reuse of previous trial code.
- Record whether each participant has previous LangGraph/FastAPI experience; do not extrapolate from one highly experienced developer.
- Suggested minimum: five independent consenting pilot participants, ideally from more than one team; if fewer, report only exploratory observations.
- Record objective completion, tests passing, total active minutes, approach and trial order. Stop/cap an unfinished trial at a predeclared 120-minute limit, and mark **incomplete**, not as a completed time.

## Reporting discipline

- Compare **only successful, comparable runs** for time-to-completion. Report completion rate and incomplete runs separately to avoid survivor bias.
- Include sample count, median, range, environment, and time spent on one-time installation separately.
- Relative reduction for matched comparable medians: `(manual_median - AET_median) / manual_median * 100%` when manual median is positive.
- Report both absolute minutes and percentage; never use CI milliseconds as a surrogate for human minutes.
- Don't invent observations, participant counts, cross-team adoption, or promotion impact.

## Data handling

Use entirely synthetic demonstration data. Do not include usernames, machine hostnames, credentials, client artifacts or company IP in uploaded benchmark results. Raw trial results may stay local if employer policy requires.
