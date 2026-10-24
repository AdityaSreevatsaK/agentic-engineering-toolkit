"""CLI for generating local-first agent projects."""
import argparse
from .generator import GenerationError, generate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentkit", description="Generate local-first agent applications")
    subparsers = parser.add_subparsers(dest="command", required=True)
    new = subparsers.add_parser("new", help="Generate a project")
    new.add_argument("name", help="Lowercase hyphenated project name")
    new.add_argument("--template", default="tool-agent", choices=["tool-agent"])
    new.add_argument("--provider", default="mock", choices=["mock"])
    new.add_argument("--output-dir", default=".", help="Parent folder for generated project")
    args = parser.parse_args(argv)
    if args.command == "new":
        try:
            path = generate(args.name, output_dir=args.output_dir, template=args.template, provider=args.provider)
        except GenerationError as exc:
            parser.exit(2, f"error: {exc}\n")
        print(f"Created {path}")
        print(f'Next: cd {path.name} && python -m pip install -e ".[dev]" && python -m pytest')
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
