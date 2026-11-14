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
- CI passes `--jobs 2`, allowing two *independent* generated projects to progress concurrently in separate directories and Python interpreters.
- The same four apps still execute real installs, `pip check`, their entire generated test suites, a mock ASGI request probe and dependency-resolution capture.
- A new root regression test uses a two-party barrier to verify that concurrency actually occurs, while checking four unique interpreter paths, the full stage matrix, the same deterministic registry order and complete evidence output.
- There are no new Actions workflows, check names, external data, paid inference calls or new packages.

Potential trade-offs: concurrent pip operations may compete for runner CPU, download bandwidth or Windows file-system resources; wall-clock duration may stay flat or worsen. File-level pip operations take place in separate app projects and virtual environments, with pip's standard shared cache. If the complete CI matrix fails or consistently slows down, revert or tune `--jobs` rather than claiming improvement.

## Verification required before merge

1. Confirm the root parallelism regression tests pass on Windows/Linux × Python 3.11/3.12, including the real source generator and mocked subprocess tests.
2. Confirm every runner produces four named `PASS isolated install:` lines and four resolved dependency files, and that all isolated mock ASGI probes pass.
3. Confirm the complete 23-pair matrix and deep-event sweeps remain green, along with all legacy suites and the fifth static-quality check.
4. Inspect the new final-head timestamped job logs and compare *like-for-like* isolated-install stage durations with the table above. Quantify observed effects rather than guaranteeing a speed-up.
5. Verify the post-merge `master` run and retain any remaining limitations. GitHub runner variance prevents reliable production performance claims.

**Status at authoring:** Baseline run inspected and scheduling/test patch committed on `perf/bounded-isolated-install-parallelism`. No PR performance results are asserted here until actually observed.
