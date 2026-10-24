"""Simple deterministic LangGraph flow; replace mock node when adding a model."""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class AgentState(TypedDict):
    question: str
    answer: str


def respond(state: AgentState) -> dict[str, str]:
    return {"answer": f"Mock response to: {state['question']}"}


def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("respond", respond)
    builder.add_edge(START, "respond")
    builder.add_edge("respond", END)
    return builder.compile()


graph = build_graph()
