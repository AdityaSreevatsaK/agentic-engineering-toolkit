"""Bounded Windows corpus-snapshot retries; malformed or unsafe data still fail."""
import pytest

from app import knowledge


def test_transient_file_read_denials_recover_without_serving_stale_data(monkeypatch, tmp_path):
    corpus = tmp_path / "knowledge.jsonl"
    corpus.write_text('{"id":"new","text":"A complete new policy."}\n', encoding="utf-8")
    knowledge._cached_documents.cache_clear()
    monkeypatch.setattr(knowledge, "_READ_ATTEMPTS", 4)
    delays = []
    monkeypatch.setattr(knowledge, "sleep", delays.append)
    real_read = knowledge.Path.read_text
    calls = []

    def occasionally_denied(path, *args, **kwargs):
        if path == corpus:
            calls.append(1)
            if len(calls) < 3:
                raise PermissionError("synthetic-Windows-sharing-lock")
        return real_read(path, *args, **kwargs)

    monkeypatch.setattr(knowledge.Path, "read_text", occasionally_denied)
    documents = knowledge.load_documents(corpus)
    assert [d.id for d in documents] == ["new"]
    assert len(calls) == 3
    assert delays == [0.01, 0.01]


def test_permanent_read_denial_fails_closed_after_finite_retries(monkeypatch, tmp_path):
    corpus = tmp_path / "knowledge.jsonl"
    corpus.write_text('{"id":"new","text":"Safe content"}\n', encoding="utf-8")
    knowledge._cached_documents.cache_clear()
    monkeypatch.setattr(knowledge, "_READ_ATTEMPTS", 3)
    pauses = []
    monkeypatch.setattr(knowledge, "sleep", pauses.append)
    real_read = knowledge.Path.read_text
    attempts = []

    def denied(path, *args, **kwargs):
        if path == corpus:
            attempts.append(1)
            raise PermissionError("synthetic-permanent-denial")
        return real_read(path, *args, **kwargs)

    monkeypatch.setattr(knowledge.Path, "read_text", denied)
    with pytest.raises(knowledge.KnowledgeError, match="unreadable"):
        knowledge.load_documents(corpus)
    assert len(attempts) == 3
    assert pauses == [0.01, 0.01]


def test_transient_missing_path_during_atomic_swap_is_bounded(monkeypatch, tmp_path):
    corpus = tmp_path / "knowledge.jsonl"
    corpus.write_text('{"id":"returns","text":"Sample return policy."}\n', encoding="utf-8")
    knowledge._cached_documents.cache_clear()
    monkeypatch.setattr(knowledge, "_READ_ATTEMPTS", 3)
    pauses = []
    monkeypatch.setattr(knowledge, "sleep", pauses.append)
    real_is_file = knowledge.Path.is_file
    attempts = []

    def sometimes_missing(path):
        if path == corpus:
            attempts.append(1)
            if len(attempts) < 3:
                return False
        return real_is_file(path)

    monkeypatch.setattr(knowledge.Path, "is_file", sometimes_missing)
    assert knowledge.load_documents(corpus)[0].id == "returns"
    assert len(attempts) == 3
    assert pauses == [0.01, 0.01]


def test_malformed_jsonl_and_symlinks_are_never_retried(monkeypatch, tmp_path):
    corpus = tmp_path / "knowledge.jsonl"
    corpus.write_text("{invalid-json\n", encoding="utf-8")
    knowledge._cached_documents.cache_clear()
    monkeypatch.setattr(knowledge, "_READ_ATTEMPTS", 8)
    delays = []
    monkeypatch.setattr(knowledge, "sleep", delays.append)
    with pytest.raises(knowledge.KnowledgeError, match="invalid JSONL"):
        knowledge.load_documents(corpus)
    assert delays == []

    original_is_symlink = knowledge.Path.is_symlink
    monkeypatch.setattr(
        knowledge.Path, "is_symlink",
        lambda path: path == corpus or original_is_symlink(path),
    )
    with pytest.raises(knowledge.KnowledgeError, match="symbolic link"):
        knowledge.load_documents(corpus)
    assert delays == []
