"""Platform-level regression tests for atomic, no-replace project publication."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from aet_scaffolder import generator
from aet_scaffolder.generator import GenerationError, generate


@pytest.mark.parametrize("claim", ["empty", "populated", "dangling-symlink"])
def test_competing_claim_at_final_publication_is_never_replaced(tmp_path, monkeypatch, claim):
    """Exercise the last micro-window after the old post-staging check."""
    target = tmp_path / "demo"
    publish = generator._publish_without_replacing

    def claim_during_publish(staging, destination):
        assert destination == target
        if claim == "dangling-symlink":
            try:
                target.symlink_to(tmp_path / "missing", target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                pytest.skip(f"Symlink creation is unavailable: {exc}")
        else:
            target.mkdir()
            if claim == "populated":
                (target / "marker.txt").write_text("keep", encoding="utf-8")
        publish(staging, destination)

    monkeypatch.setattr(generator, "_publish_without_replacing", claim_during_publish)
    with pytest.raises(GenerationError, match="overwrite"):
        generate("demo", output_dir=tmp_path)

    if claim == "dangling-symlink":
        assert target.is_symlink()
    elif claim == "populated":
        assert (target / "marker.txt").read_text(encoding="utf-8") == "keep"
    else:
        assert target.is_dir()
        assert list(target.iterdir()) == []
    assert not list(tmp_path.glob(".aet-*"))


def test_concurrent_generation_exactly_one_success(tmp_path, monkeypatch):
    """All workers reach staging together; only one may publish the same name."""
    workers = 6
    barrier = Barrier(workers)
    copy = generator._copy_template

    def synchronised_copy(source, destination, replacements):
        # Only synchronise once per worker, not recursive template copy calls.
        if destination.parent.name.startswith(".aet-"):
            barrier.wait(timeout=20)
        return copy(source, destination, replacements)

    monkeypatch.setattr(generator, "_copy_template", synchronised_copy)

    def create(_):
        try:
            return generate("contended", output_dir=tmp_path)
        except GenerationError:
            return None

    with ThreadPoolExecutor(max_workers=workers) as executor:
        outcomes = list(executor.map(create, range(workers)))

    assert sum(path is not None for path in outcomes) == 1, outcomes
    assert (tmp_path / "contended" / ".aet-template.json").is_file()
    assert not list(tmp_path.glob(".aet-*"))
