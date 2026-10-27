"""Pure unit tests that do not require a language model."""
from app.tools import get_order_status


def test_known_demo_order():
    assert get_order_status("ORD-1001") == "Demo order ORD-1001 status: shipped."


def test_unknown_demo_order():
    assert get_order_status("ORD-9999") == "Demo order ORD-9999 was not found."
