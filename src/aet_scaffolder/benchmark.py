"""Local scaffolder generation and validation timings (not human productivity)."""
import math
import platform
import statistics
import tempfile
import time

from .generator import generate
from .validator import validate_project


def _stats(values):
    ordered = sorted(values)
    return {
        "median_ms": round(statistics.median(ordered), 3),
        "p95_ms": round(ordered[math.ceil(.95 * len(ordered)) - 1], 3),
    }


def run(runs=10, warmups=2, provider="mock"):
    if type(runs) is not int or not 1 <= runs <= 50:
        raise ValueError("runs must be 1..50")
    if type(warmups) is not int or not 0 <= warmups <= 10:
        raise ValueError("warmups must be 0..10")
    samples = []
    with tempfile.TemporaryDirectory(prefix="aet-benchmark-") as tmp:
        for i in range(runs + warmups):
            t0 = time.perf_counter_ns()
            project = generate("trial-" + str(i).zfill(4), output_dir=tmp, provider=provider)
            t1 = time.perf_counter_ns()
            if not validate_project(project).ok:
                raise RuntimeError("Generated project failed validation")
            t2 = time.perf_counter_ns()
            if i >= warmups:
                samples.append({
                    "generation_ms": round((t1-t0)/1e6, 3),
                    "validation_ms": round((t2-t1)/1e6, 3),
                    "total_ms": round((t2-t0)/1e6, 3)
                })
    return {
        "environment": {"os": platform.system(), "python": platform.python_version()},
        "provider": provider,
        "runs": runs,
        "warmups": warmups,
        "samples": samples,
        "summary": {key: _stats([sample[key] for sample in samples]) for key in ("generation_ms", "validation_ms", "total_ms")},
        "scope": "file generation and static validation only; not developer time saved",
    }
