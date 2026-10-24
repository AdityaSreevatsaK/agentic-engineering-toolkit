import pytest
from aet_scaffolder.generator import generate, GenerationError
from aet_scaffolder.cli import main


def test_generate_full_tree(tmp_path):
    root = generate("demo-agent", output_dir=tmp_path)
    assert root.name == "demo-agent"
    assert (root / "app" / "main.py").is_file()
    assert (root / "app" / "workflow.py").is_file()
    assert (root / ".gitignore").is_file()
    assert 'name = "demo-agent"' in (root / "pyproject.toml").read_text()
    for source in root.rglob("*.py"):
        compile(source.read_text(encoding="utf-8"), str(source), "exec")


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


def test_unknown_provider_rejected(tmp_path):
    with pytest.raises(GenerationError):
        generate("demo", output_dir=tmp_path, provider="openai")


def test_missing_output_dir(tmp_path):
    with pytest.raises(GenerationError):
        generate("demo", output_dir=tmp_path / "missing")


def test_cli(tmp_path, capsys):
    assert main(["new", "sample-agent", "--output-dir", str(tmp_path)]) == 0
    assert "Created" in capsys.readouterr().out
    assert (tmp_path / "sample-agent" / "README.md").exists()
