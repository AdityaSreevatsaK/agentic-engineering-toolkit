"""Command-line interface for local-first agent project scaffolding."""
import argparse
import json

from . import __version__
from .generator import GenerationError, SUPPORTED_PROVIDERS, generate
from .registry import DEFAULT_TEMPLATE, SUPPORTED_TEMPLATES, TEMPLATES
from .validator import validate_project


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentkit", description="Generate and verify local-first agent projects")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    new = subparsers.add_parser("new", help="Generate a ready-to-run project")
    new.add_argument("name", help="Lowercase hyphenated project name")
    new.add_argument("--template", default=DEFAULT_TEMPLATE, choices=SUPPORTED_TEMPLATES)
    new.add_argument("--provider", default="mock", choices=SUPPORTED_PROVIDERS)
    new.add_argument("--model", help="Local Ollama model identifier (only with --provider ollama)")
    new.add_argument("--output-dir", default=".", help="Parent directory for generated project")

    subparsers.add_parser("list", help="List the supported templates and model providers")
    doctor = subparsers.add_parser("doctor", help="Safely inspect generated project files and Python syntax")
    doctor.add_argument("path", nargs="?", default=".", help="Generated project directory (default: current)")
    doctor.add_argument("--json", action="store_true", help="Print machine-readable validation results")

    args = parser.parse_args(argv)
    if args.command == "list":
        for spec in TEMPLATES.values():
            print(f"Template: {spec.name}")
        print("Providers: " + ", ".join(SUPPORTED_PROVIDERS))
        print(f"Default: {DEFAULT_TEMPLATE} with mock (offline, deterministic)")
        return 0
    if args.command == "doctor":
        report = validate_project(args.path)
        if args.json:
            print(json.dumps(report.as_dict(), indent=2))
        else:
            print(f"Checking generated project: {report.path}")
            for check in report.checks:
                print(f"  {'PASS' if check.passed else 'FAIL'} {check.name}: {check.message}")
            print("Result: PASS" if report.ok else "Result: FAIL")
        return 0 if report.ok else 1
    if args.command == "new":
        try:
            path = generate(
                args.name,
                output_dir=args.output_dir,
                template=args.template,
                provider=args.provider,
                model=args.model,
            )
        except GenerationError as exc:
            parser.exit(2, f"error: {exc}\n")
        print(f"Created {path}")
        print(f"Verify: agentkit doctor {path}")
        print(f'Next: cd {path.name} && python -m pip install -e ".[dev]" && python -m pytest')
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
