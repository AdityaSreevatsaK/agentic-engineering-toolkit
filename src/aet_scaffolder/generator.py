"""Generate a local-first agent project from a registered bundled template."""
import json
import re
import tempfile
from importlib.resources import files
from pathlib import Path

from .registry import DEFAULT_TEMPLATE, MANIFEST_FILE, MANIFEST_VERSION, get_template

NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
MODEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
DEFAULT_OLLAMA_MODEL = "llama3.2:1b"
# Keep this export for callers of the existing generator module.
SUPPORTED_PROVIDERS = ("mock", "ollama", "bedrock", "openai", "azure-openai", "anthropic")


class GenerationError(ValueError):
    """Raised when project creation cannot safely proceed."""


def generate(
    name: str,
    *,
    output_dir: str | Path = ".",
    template: str = DEFAULT_TEMPLATE,
    provider: str = "mock",
    model: str | None = None,
) -> Path:
    if not NAME_PATTERN.fullmatch(name):
        raise GenerationError("name must be lowercase kebab-case, e.g. 'demo-agent'")
    try:
        spec = get_template(template)
    except ValueError as exc:
        raise GenerationError(str(exc)) from exc
    if provider not in spec.providers:
        raise GenerationError(
            f"provider for '{template}' must be one of: {', '.join(spec.providers)}"
        )
    if provider != "ollama" and model is not None:
        raise GenerationError("--model can only be used with --provider ollama")
    selected_model = model if model is not None else DEFAULT_OLLAMA_MODEL
    if not MODEL_PATTERN.fullmatch(selected_model):
        raise GenerationError("invalid Ollama model name (no spaces or control characters allowed)")
    parent = Path(output_dir).resolve()
    if not parent.is_dir():
        raise GenerationError(f"output directory does not exist: {parent}")
    target = parent / name
    if target.exists():
        raise GenerationError(f"refusing to overwrite existing path: {target}")
    source = files("aet_scaffolder").joinpath("templates", spec.directory)
    replacements = {
        "__PROJECT_NAME__": name,
        "__PACKAGE_NAME__": name.replace("-", "_"),
        "__PROVIDER__": provider,
        "__OLLAMA_MODEL__": selected_model,
    }
    try:
        with tempfile.TemporaryDirectory(prefix=".aet-", dir=str(parent)) as temporary:
            staging = Path(temporary) / name
            staging.mkdir()
            _copy_template(source, staging, replacements)
            (staging / MANIFEST_FILE).write_text(
                json.dumps(
                    {"schema_version": MANIFEST_VERSION, "template": spec.name},
                    indent=2,
                ) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            staging.rename(target)
    except OSError as exc:
        raise GenerationError(f"could not generate project: {exc}") from exc
    return target


def _copy_template(src, dest: Path, replacements: dict[str, str]) -> None:
    for item in src.iterdir():
        if item.name == "__pycache__":
            continue
        path = dest / item.name.replace("_dot_", ".")
        if item.is_dir():
            path.mkdir()
            _copy_template(item, path, replacements)
        else:
            content = item.read_text(encoding="utf-8")
            for key, value in replacements.items():
                content = content.replace(key, value)
            path.write_text(content, encoding="utf-8", newline="\n")
