"""Deterministic, dependency-free template renderer for the M1 prototype."""
from importlib.resources import files
from pathlib import Path
import re

NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


class GenerationError(ValueError):
    """Raised when project creation cannot safely proceed."""


def generate(name: str, *, output_dir: str | Path = ".", template: str = "tool-agent", provider: str = "mock") -> Path:
    if not NAME_PATTERN.fullmatch(name):
        raise GenerationError("name must be lowercase kebab-case, e.g. 'demo-agent'")
    if template != "tool-agent" or provider != "mock":
        raise GenerationError("M1 supports only --template tool-agent --provider mock")
    parent = Path(output_dir).resolve()
    if not parent.is_dir():
        raise GenerationError(f"output directory does not exist: {parent}")
    target = parent / name
    if target.exists():
        raise GenerationError(f"refusing to overwrite existing path: {target}")
    source = files("aet_scaffolder").joinpath("templates", "tool_agent")
    replacements = {"__PROJECT_NAME__": name, "__PACKAGE_NAME__": name.replace("-", "_")}
    # Stage before publishing so rendering errors do not leave half-written projects.
    import tempfile
    try:
        with tempfile.TemporaryDirectory(prefix=".aet-", dir=str(parent)) as temporary:
            staging = Path(temporary) / name
            staging.mkdir()
            _copy_template(source, staging, replacements)
            staging.rename(target)
    except OSError as exc:
        raise GenerationError(f"could not generate project: {exc}") from exc
    return target


def _copy_template(src, dest: Path, replacements: dict[str, str]) -> None:
    for item in src.iterdir():
        if item.name == "__pycache__":
            continue
        new_name = item.name.replace("_dot_", ".")
        path = dest / new_name
        if item.is_dir():
            path.mkdir()
            _copy_template(item, path, replacements)
        else:
            content = item.read_text(encoding="utf-8")
            for key, value in replacements.items():
                content = content.replace(key, value)
            path.write_text(content, encoding="utf-8", newline="\n")
