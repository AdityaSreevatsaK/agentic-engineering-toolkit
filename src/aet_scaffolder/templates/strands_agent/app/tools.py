"""Synthetic, read-only order lookup. No external tools, networks or real records."""
import re

from strands import tool

_ORDERS = {
    "ORD-1001": "shipped",
    "ORD-1002": "processing",
    "ORD-1003": "delivered",
}
_ID = re.compile(r"ORD-[0-9]{4}")


@tool
def get_order_status(order_id: str) -> str:
    """Look up a **synthetic** demo order by ID, e.g. ORD-1001.

    Args:
        order_id: An ID in the form ORD-1001, not a real customer identifier.
    """
    if not _ID.fullmatch(order_id):
        return "Invalid sample order ID; use ORD- followed by four digits."
    status = _ORDERS.get(order_id)
    if status is None:
        return f"Sample order {order_id} was not found."
    return f"Sample order {order_id} status: {status}."
