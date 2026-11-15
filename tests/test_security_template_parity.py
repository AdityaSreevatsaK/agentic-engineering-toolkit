"""Every standalone generated app must retain identical security foundations."""
from importlib.resources import files


def test_shared_foundation_and_security_tests_are_identical():
    root = files("aet_scaffolder").joinpath("templates")
    names = ("tool_agent", "langgraph_rag", "strands_agent", "llamaindex_rag")
    for path in ("app/foundation.py", "tests/test_security.py"):
        variants = [root.joinpath(name, path).read_text(encoding="utf-8") for name in names]
        assert len(set(variants)) == 1, f"Template security drift: {path}"
