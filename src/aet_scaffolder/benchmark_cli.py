"""Command line entry point for reproducible local microbenchmarking."""
import argparse
import csv
import json
import sys
from pathlib import Path

from .benchmark import run


def main(argv=None):
    parser = argparse.ArgumentParser(prog="agentkit-benchmark")
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--provider", choices=("mock", "ollama"), default="mock")
    parser.add_argument("--json-out", help="Write JSON to a new file")
    parser.add_argument("--csv-out", help="Write sample CSV to a new file")
    args = parser.parse_args(argv)
    try:
        result = run(runs=args.runs, warmups=args.warmups, provider=args.provider)
        targets = [Path(p) for p in (args.json_out, args.csv_out) if p]
        if len({p.resolve() for p in targets}) != len(targets):
            raise ValueError("Output filenames must differ")
        if any(p.exists() for p in targets):
            raise ValueError("Existing reports will not be overwritten")
        if args.json_out:
            with open(args.json_out, "x", encoding="utf-8") as output:
                json.dump(result, output, indent=2)
        if args.csv_out:
            with open(args.csv_out, "x", newline="", encoding="utf-8") as output:
                writer = csv.DictWriter(output, fieldnames=("generation_ms", "validation_ms", "total_ms"))
                writer.writeheader()
                writer.writerows(result["samples"])
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"Benchmark failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
