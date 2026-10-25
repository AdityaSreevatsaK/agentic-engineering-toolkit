"""Local ingestion is bounded, deterministic and never overwrites a corpus."""
import json

import pytest

from app.ingest import chunk_text, ingest_directory, main
from app.knowledge import KnowledgeError, load_documents


def test_ingest_text_and_markdown(tmp_path):
    folder = tmp_path / "source"
    folder.mkdir()
    (folder / "policy.txt").write_text("return policy " * 80, encoding="utf-8")
    (folder / "support.md").write_text("help desk hours", encoding="utf-8")
    output = tmp_path / "corpus.jsonl"
    count = ingest_directory(folder, output, limit=120)
    assert count >= 2
    docs = load_documents(output)
    assert len(docs) == count
    assert all(d.id.startswith(("policy-", "support-")) for d in docs)
    assert all(len(d.text) <= 120 for d in docs)


def test_cli_writes_new_file(tmp_path, capsys):
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "faq.md").write_text("synthetic FAQ text", encoding="utf-8")
    out = tmp_path / "index.jsonl"
    assert main(["--input", str(folder), "--output", str(out)]) == 0
    assert out.exists()
    assert "Wrote 1 passages" in capsys.readouterr().out


def test_existing_output_is_never_overwritten(tmp_path):
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "faq.txt").write_text("dummy sample", encoding="utf-8")
    out = tmp_path / "index.jsonl"
    out.write_text("existing\n", encoding="utf-8")
    with pytest.raises(KnowledgeError, match="overwrite"):
        ingest_directory(folder, out)
    assert out.read_text(encoding="utf-8") == "existing\n"


def test_long_word_rejected():
    with pytest.raises(KnowledgeError, match="larger"):
        chunk_text("a" * 101, limit=100)


def test_empty_folder_rejected(tmp_path):
    with pytest.raises(KnowledgeError, match="between 1 and 30"):
        ingest_directory(tmp_path, tmp_path / "out.jsonl")
