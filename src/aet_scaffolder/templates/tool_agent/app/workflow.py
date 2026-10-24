"""Deterministic LangGraph workflow demonstrating an actual tool call.

This M1 sample deliberately uses rule-based routing, not a language model.
"""
import re
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from .tools import get_order_status

_ORDER_COMMAND = re.compile(r"\s*order\s+status\s+(ORD-\d{4})\s*", re.IGNORECASE)


class AgentState(TypedDict, total=False):
    question: str
    answer: str
    order_id: str | None
    tool_used: str | None


def detect_order_request(state: AgentState) -> dict[str, str | None]:
    match = _ORDER_COMMAND.fullmatch(state["question"])
    return {"order_id": match.group(1).upper() if match else None}


def choose_route(state: AgentState) -> str:
    return "lookup_order" if state.get("order_id") else "respond"


def lookup_order(state: AgentState) -> dict[str, str]:
    return {
        "answer": get_order_status(state["order_id"]),
        "tool_used": "get_order_status",
    }


def respond(state: AgentState) -> dict[str, str | None]:
    return {
        "answer": f"Mock response to: {state['question']}",
        "tool_used": None,
    }


def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("detect_order_request", detect_order_request)
    builder.add_node("lookup_order", lookup_order)
    builder.add_node("respond", respond)
    builder.add_edge(START, "detect_order_request")
    builder.add_conditional_edges(
        "detect_order_request",
        choose_route,
        {"lookup_order": "lookup_order", "respond": "respond"},
    )
    builder.add_edge("lookup_order", END)
    builder.add_edge("respond", END)
    return builder.compile()


graph = build_graph()
