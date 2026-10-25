"""Construct a REAL Strands Agent with offline scripted or Amazon Bedrock provider."""
from strands import Agent
from strands.models import BedrockModel

from .config import Settings
from .offline_model import OfflineModel
from .tools import get_order_status

_SYSTEM = (
    "You are a synthetic order status demo assistant. "
    "Use get_order_status only for example ORD-#### identifiers. "
    "Never claim access to real customer orders or external services."
)


def create_model(settings: Settings):
    if settings.provider == "mock":
        return OfflineModel()
    return BedrockModel(
        model_id=settings.bedrock_model_id,
        region_name=settings.aws_region,
        streaming=False,
    )


def build_agent(settings: Settings) -> Agent:
    """A new Agent per request avoids leaking conversation context across callers."""
    return Agent(
        model=create_model(settings),
        tools=[get_order_status],
        system_prompt=_SYSTEM,
        callback_handler=None,
    )


def run_agent(question: str, settings: Settings) -> tuple[str, bool]:
    """Return final text and whether the agent actually requested the synthetic tool."""
    agent = build_agent(settings)
    result = agent(question)
    used_tool = any(
        "toolUse" in block
        for message in agent.messages
        for block in message.get("content", [])
        if isinstance(block, dict)
    )
    return str(result), used_tool
