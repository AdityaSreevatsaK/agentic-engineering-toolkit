"""Read-only, dependency-free verification of generated project structure.

The doctor command parses source without importing or executing generated modules.
It can validate generated projects even if their dependencies are not installed.
"""
from __future__ import annotations

import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path

REQUIRED_FILES = (
    "README.md",
    ".gitignore",
    ".env.example",
    "pyproject.toml",
    "app/__init__.py",
    "app/config.py",
    "app/main.py",
    "app/providers.py",
    "app/tools.py",
    "app/workflow.py",
    "tests/test_app.py",
    "tests/test_providers.py",
    "tests/test_tools.py",
)
REQUIRED_DEPENDENCIES = {"fastapi", "langgraph", "uvicorn", "pydantic-settings"}


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    message: str

    def as_dict(self) -> dict[str, str | bool]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationReport:
    path: str
    checks: tuple[Check, ...]

    @property
    def ok(self) -> bool:
        return all(check.passed for check in self.checks)

    def as_dict(self) -> dict:
        return {
            "path": self.path,
            "ok": self.ok,
            "checks": [check.as_dict() for check in self.checks],
        }


def _text_file(root: Path, relative: str) -> str:
    """Read a required file without following links or accepting oversized input."""
    file = root / relative
    if file.is_symlink() or not file.is_file():
        raise ValueError(f"{relative}: missing, not a file, or a symbolic link")
    if file.stat().st_size > 1_000_000:
        raise ValueError(f"{relative}: larger than 1 MB")
    return file.read_text(encoding="utf-8")


def validate_project(path: str | Path) -> ValidationReport:
    """Inspect expected files, metadata, and Python syntax without running code."""
    root = Path(path).expanduser().absolute()
    checks: list[Check] = []
    if not root.is_dir() or root.is_symlink():
        checks.append(Check("project_directory", False, "Project directory is missing or is a symbolic link"))
        return ValidationReport(str(root), tuple(checks))

    for relative in REQUIRED_FILES:
        try:
            _text_file(root, relative)
        except (ValueError, OSError, UnicodeError) as exc:
            checks.append(Check(f"file:{relative}", False, str(exc)))
        else:
            checks.append(Check(f"file:{relative}", True, "Present and readable"))

    try:
        data = tomllib.loads(_text_file(root, "pyproject.toml"))
        project = data["project"]
        name = project["name"]
        dependencies = project.get("dependencies", [])
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Project metadata is missing a nonempty name")
        if not isinstance(dependencies, list):
            raise ValueError("Project dependencies must be a list")
        installed = {
            dep.split(">")[0].split("<")[0].split("=")[0].split("!")[0].split("[")[0].strip().lower()
            for dep in dependencies if isinstance(dep, str)
        }
        missing = sorted(REQUIRED_DEPENDENCIES - installed)
        if missing:
            raise ValueError("Missing generated app dependencies: " + ", ".join(missing))
        checks.append(Check("project_metadata", True, f"Valid metadata for {name}"))
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, tomllib.TOMLDecodeError) as exc:
        checks.append(Check("project_metadata", False, str(exc)))

    try:
        config = _text_file(root, ".env.example")
        fields = ("AET_PROVIDER=", "AET_OLLAMA_MODEL=", "AET_OLLAMA_BASE_URL=")
        missing = [field for field in fields if not any(line.startswith(field) for line in config.splitlines())]
        if missing:
            raise ValueError("Missing sample configuration: " + ", ".join(missing))
        checks.append(Check("sample_configuration", True, "Provider settings documented"))
    except (OSError, UnicodeError, ValueError) as exc:
        checks.append(Check("sample_configuration", False, str(exc)))

    try:
        for folder in ("app", "tests"):
            if (root / folder).is_symlink():
                raise ValueError(f"Generated {folder} directory may not be a symbolic link")
        # Only inspect these expected source trees. A generated project may contain
        # arbitrary other data; doctor is deliberately read-only.
        paths = list((root / "app").rglob("*.py")) + list((root / "tests").rglob("*.py"))
        if not paths:
            raise ValueError("No generated Python source files found")
        for source in paths:
            relative = source.relative_to(root).as_posix()
            compile(_text_file(root, relative), str(source), "exec")
        checks.append(Check("python_syntax", True, f"{len(paths)} source files parsed"))
    except (OSError, UnicodeError, ValueError, SyntaxError) as exc:
        checks.append(Check("python_syntax", False, str(exc)))

    return ValidationReport(str(root), tuple(checks))
