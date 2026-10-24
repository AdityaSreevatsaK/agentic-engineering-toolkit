"""Synthetic local business tool; no credentials, network or real customer records."""

# Demo-only fixture: synthetic IDs and statuses.
ORDER_STATUSES: dict[str, str] = {
    "ORD-1001": "shipped",
    "ORD-1002": "processing",
    "ORD-1003": "delivered",
}


def get_order_status(order_id: str) -> str:
    """Return a deterministic order status from synthetic demo data."""
    status = ORDER_STATUSES.get(order_id)
    if status is None:
        return f"Demo order {order_id} was not found."
    return f"Demo order {order_id} status: {status}."
