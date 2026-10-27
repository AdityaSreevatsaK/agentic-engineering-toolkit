import pytest

from aet_scaffolder.cli import main
from aet_scaffolder.generator import GenerationError, generate


def test_generate_full_tree(tmp_path):
    root = generate("demo-agent", output_dir=tmp_path)
    assert root.name == "demo-agent"
    assert (root / "app" / "main.py").is_file()
    assert (root / "app" / "providers.py").is_file()
    assert (root / "app" / "config.py").is_file()
    assert (root / ".gitignore").is_file()
    assert (root / ".env.example").is_file()
    assert 'name = "demo-agent"' in (root / "pyproject.toml").read_text()
    assert "AET_PROVIDER=mock" in (root / ".env.example").read_text()
    for source in root.rglob("*.py"):
        compile(source.read_text(encoding="utf-8"), str(source), "exec")


def test_generate_ollama_defaults(tmp_path):
    root = generate("local-agent", output_dir=tmp_path, provider="ollama")
    config = (root / ".env.example").read_text()
    assert "AET_PROVIDER=ollama" in config
    assert "AET_OLLAMA_MODEL=llama3.2:1b" in config
    assert "provider: Literal" in (root / "app" / "config.py").read_text()


def test_generate_custom_model(tmp_path):
    root = generate("local-agent", output_dir=tmp_path, provider="ollama", model="qwen2.5:0.5b")
    assert "AET_OLLAMA_MODEL=qwen2.5:0.5b" in (root / ".env.example").read_text()


def test_reject_invalid_names(tmp_path):
    for name in ("../oops", "/tmp/evil", "bad_name", "Hello", "", "a--b"):
        with pytest.raises(GenerationError):
            generate(name, output_dir=tmp_path)


def test_do_not_overwrite_existing_project(tmp_path):
    first = generate("demo", output_dir=tmp_path)
    marker = first / "data.txt"
    marker.write_text("keep")
    with pytest.raises(GenerationError, match="overwrite"):
        generate("demo", output_dir=tmp_path)
    assert marker.read_text() == "keep"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"provider": "not-a-provider"},
        {"provider": "mock", "model": "llama3.2"},
        {"provider": "ollama", "model": "bad model"},
        {"provider": "ollama", "model": "bad\nMODEL"},
        {"template": "unknown"},
    ],
)
def test_invalid_options_rejected(tmp_path, kwargs):
    with pytest.raises(GenerationError):
        generate("demo", output_dir=tmp_path, **kwargs)


def test_missing_output_dir(tmp_path):
    with pytest.raises(GenerationError):
        generate("demo", output_dir=tmp_path / "missing")


def test_cli_mock(tmp_path, capsys):
    assert main(["new", "sample-agent", "--output-dir", str(tmp_path)]) == 0
    assert "Created" in capsys.readouterr().out
    assert (tmp_path / "sample-agent" / "README.md").exists()


def test_cli_ollama(tmp_path):
    assert main(["new", "sample-agent", "--provider", "ollama", "--model", "qwen2.5:0.5b", "--output-dir", str(tmp_path)]) == 0
    assert "AET_PROVIDER=ollama" in (tmp_path / "sample-agent" / ".env.example").read_text()
