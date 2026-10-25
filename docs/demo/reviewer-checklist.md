# M7 independent engineering review checklist

**Status:** Blank review guide. No review or adoption has happened simply because this file exists.

## Reviewer tasks

- [ ] On an approved Windows or Linux environment, install Python 3.11/3.12 and the three packages as documented.
- [ ] Execute `python scripts/run_demo.py`, note exit status and check counts.
- [ ] Confirm the temporary project validates and no model download, cloud request or public server is required.
- [ ] Read the standalone Quality Kit usage and identify one real testing scenario it might simplify.
- [ ] Read the Provider Contract and identify one missing portability requirement before considering cloud work.
- [ ] Try `agentkit new review-agent --provider mock`, then `agentkit doctor review-agent`.
- [ ] Record independent reproducibility, confusing instructions, defects and possible adoption constraints.

## Feedback prompts

Record the following as anonymous observations, not fabricated scores:

- Could you complete the demo on your own? If not, at which step?
- What prerequisite or CLI instruction was unclear?
- Which asset, if any, seems reusable in your own work?
- What security, performance, support or ownership issues would block real adoption?
- Which missing feature would most improve developer usability?
- Would you consider a supervised internal pilot after IP/ownership approvals?

Separate **technical reproducibility** from **developer productivity**. Actual developer-hours comparisons follow `docs/benchmarks/study_protocol.md` and require controlled trials. Do not commit identifiable participant information or company data.
