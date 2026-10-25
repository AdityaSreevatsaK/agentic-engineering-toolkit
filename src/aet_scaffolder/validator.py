"""Read-only, dependency-free verification of generated project structure.

Project manifests select the registered validation profile. Projects generated
before M11 have no manifest and retain the original tool-agent validation.
Doctor parses source without importing or executing generated modules.
"""
from __future__ import annotations

import json
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path

from .registry import (
    DEFAULT_TEMPLATE,
    MANIFEST_FILE,
    MANIFEST_VERSION,
    TemplateSpec,
    get_template,
)

# Public legacy constants remain available for existing integrations.
_LEGACY_SPEC = get_template(DEFAULT_TEMPLATE)
REQUIRED_FILES = _LEGACY_SPEC.required_files
REQUIRED_DEPENDENCIES = set(_LEGACY_SPEC.required_dependencies)


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


def _resolve_template(root: Path) -> tuple[TemplateSpec, Check]:
    marker = root / MANIFEST_FILE
    if not marker.exists() and not marker.is_symlink():
        return _LEGACY_SPEC, Check(
            "template_identity",
            True,
            f"Legacy project without manifest; using {DEFAULT_TEMPLATE} validation",
        )
    data = json.loads(_text_file(root, MANIFEST_FILE))
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int:
        raise ValueError("Invalid template manifest structure or schema version")
    if data["schema_version"] != MANIFEST_VERSION:
        raise ValueError(f"Unsupported template manifest version: {data['schema_version']}")
    name = data.get("template")
    if not isinstance(name, str):
        raise ValueError("Template manifest needs a string template name")
    spec = get_template(name)
    return spec, Check("template_identity", True, f"Registered template: {spec.name}")


def validate_project(path: str | Path) -> ValidationReport:
    """Inspect expected files, metadata, and Python syntax without running code."""
    root = Path(path).expanduser().absolute()
    checks: list[Check] = []
    if not root.is_dir() or root.is_symlink():
        checks.append(Check("project_directory", False, "Project directory is missing or is a symbolic link"))
        return ValidationReport(str(root), tuple(checks))

    try:
        spec, identity_check = _resolve_template(root)
        checks.append(identity_check)
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        checks.append(Check("template_identity", False, str(exc)))
        return ValidationReport(str(root), tuple(checks))

    for relative in spec.required_files:
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
        missing = sorted(spec.required_dependencies - installed)
        if missing:
            raise ValueError("Missing generated app dependencies: " + ", ".join(missing))
        checks.append(Check("project_metadata", True, f"Valid metadata for {name}"))
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, tomllib.TOMLDecodeError) as exc:
        checks.append(Check("project_metadata", False, str(exc)))

    try:
        config = _text_file(root, ".env.example")
        missing = [
            field
            for field in spec.required_env_fields
            if not any(line.startswith(field) for line in config.splitlines())
        ]
        if missing:
            raise ValueError("Missing sample configuration: " + ", ".join(missing))
        checks.append(Check("sample_configuration", True, "Template settings documented"))
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
