# CI efficiency investigation: bounded generated-app installation, 14 November 2026

**AET scope:** Agent Project Scaffolder only. The historical Quality Kit/Provider Contract suites remain required regression evidence, not active AET product development. Do not reduce coverage or change the five protected check names without deliberate governance.

## Baseline: observed, not estimated

Successful GitHub Actions [master run #43588281340](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions/runs/43588281340), source commit `82e4b956bfe6895cb10b398baaaaef5399d29376`, has been inspected using its actual per-job timestamped logs. Timings below are rounded elapsed seconds between consecutive step `Run` markers; they include small surrounding step transitions and should not be interpreted as isolated Python function timings.

| Environment | Four sequential isolated-venv installs + tests + API probes | Full 23-pair mock matrix | Deep-event sweep |
| --- | ---: | ---: | ---: |
| Windows 2025, Python 3.11 | 153.1 s | 30.8 s | 44.4 s |
| Windows 2025, Python 3.12 | 150.1 s | 33.4 s | 48.8 s |
| Ubuntu 24.04, Python 3.11 | 65.5 s | 18.9 s | 29.6 s |
| Ubuntu 24.04, Python 3.12 | 70.0 s | 25.8 s | 37.2 s |

The four-image Docker smoke step took approximately **57.5 s** on the Ubuntu/Python 3.11 leg only, and is deliberately retained. The main CI run finished successfully; Windows is the critical path. Existing `actions/setup-python` steps already enable pip download caching with `**/pyproject.toml`, so this change does not add redundant caching.

## Confirmed opportunity

The `scripts/isolated_install_smoke.py` runner previously verified each of the four templates **sequentially**. Each generated project already has its own source directory, `venv-<template>` environment, interpreter, dependency resolution, tests, ASGI probe and `pip freeze` output. Their default `app` module names are identical, so **merging environments is unsafe** and was not considered an acceptable optimisation.

No installation/test can be removed without losing an explicit acceptance requirement. Instead, bounded parallel scheduling is a comparatively small implementation change.

## Change under review

- Add `--jobs` (1 to 4) to the existing isolated smoke runner, defaulting to 1 for conservative local debugging.
- Ubuntu CI passes `--jobs 2`, allowing two *independent* generated projects to progress concurrently; Windows retains sequential `--jobs 1` because the first concurrent trial failed during a pip installation.
- The same four apps still execute real installs, `pip check`, their entire generated test suites, a mock ASGI request probe and dependency-resolution capture.
- A new root regression test uses a two-party barrier to verify that concurrency actually occurs, while checking four unique interpreter paths, the full stage matrix, the same deterministic registry order and complete evidence output.
- There are no new Actions workflows, check names, external data, paid inference calls or new packages.

Potential trade-offs: concurrent pip operations may compete for runner CPU, download bandwidth or Windows file-system resources; wall-clock duration may stay flat or worsen. File-level pip operations take place in separate app projects and virtual environments, with pip's standard shared cache. If the complete CI matrix fails or consistently slows down, revert or tune `--jobs` rather than claiming improvement.

## First PR trial: observed outcomes and corrective decision

[PR run #43590090293](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions/runs/43590090293) exercised two concurrent installations on **all** four runners. The root tests and quality check passed. Three of five required jobs passed, but **Windows/Python 3.12 failed**: the runner reported `tool-agent/install failed (exit status 1)` while performing concurrent independent installs. The harness intentionally omits arbitrary pip stderr from public logs, so the underlying pip error (such as a cache lock, network problem or transient package failure) **was not established**. Missing downstream matrix artifacts on that job were cascading effects. Do not claim this run was green.

| Runner | Baseline stage | Concurrent trial | Interpretation |
| --- | ---: | ---: | --- |
| Ubuntu Python 3.11 | 65.5 s | 56.9 s | Passed; 13% reduction in measured step interval |
| Ubuntu Python 3.12 | 70.0 s | 31.1 s | Passed; 56% reduction in measured step interval |
| Windows Python 3.11 | 153.1 s | 130.3 s | Passed, but limited improvement |
| Windows Python 3.12 | 150.1 s | 58.5 s to failing step exit | **Failed**, not a valid speed comparison |

**Correction under review:** Run two concurrent workers on Ubuntu only. Windows reverts to the earlier proven sequential mode, retaining all four installations, test suites, ASGI probes and evidence per runner. Full five-job CI must pass again on this corrected final head before merge; first-run Linux measurements are not final-head measurements.

## Verification required before merge

1. Confirm the root parallelism regression tests pass on Windows/Linux × Python 3.11/3.12, including the real source generator and mocked subprocess tests.
2. Confirm every runner produces four named `PASS isolated install:` lines and four resolved dependency files, and that all isolated mock ASGI probes pass.
3. Confirm the complete 23-pair matrix and deep-event sweeps remain green, along with all legacy suites and the fifth static-quality check.
4. Inspect the new final-head timestamped job logs and compare *like-for-like* isolated-install stage durations with the table above. Quantify observed effects rather than guaranteeing a speed-up.
5. Verify the post-merge `master` run and retain any remaining limitations. GitHub runner variance prevents reliable production performance claims.

**Status:** Baseline and first PR run inspected; a Windows concurrent-install failure prompted an Ubuntu-only concurrency correction. The complete corrected final-head five-job validation and post-merge measurements remain pending.
