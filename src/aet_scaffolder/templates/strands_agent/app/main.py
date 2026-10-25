"""HTTP interface for the local-first Strands example. Not public-facing."""
from fastapi import FastAPI, HTTPException
from .foundation import install_foundations
from pydantic import BaseModel, Field

from .agent import run_agent
from .config import get_settings

app = FastAPI(title="__PROJECT_NAME__", version="0.1.0")
install_foundations(app)


class InvokeRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class InvokeResponse(BaseModel):
    answer: str
    tool_used: bool
    provider: str


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness only; does not verify Bedrock credentials or model access."""
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    """Check offline configuration; Bedrock credentials are not probed."""
    try:
        settings = get_settings()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="Invalid local configuration") from exc
    if settings.provider != "mock":
        raise HTTPException(status_code=503, detail="Live Bedrock readiness has not been verified")
    return {"status": "ready"}


@app.post("/invoke", response_model=InvokeResponse)
def invoke(request: InvokeRequest) -> InvokeResponse:
    try:
        settings = get_settings()
        answer, tool_used = run_agent(request.question, settings)
    except Exception as exc:
        # Do not reveal credentials, AWS error messages, account IDs or prompts.
        raise HTTPException(
            status_code=503, detail="Agent unavailable; verify local configuration and provider access"
        ) from exc
    return InvokeResponse(answer=answer, tool_used=tool_used, provider=settings.provider)
