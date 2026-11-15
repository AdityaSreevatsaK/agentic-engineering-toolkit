"""HTTP interface for the generated local-first agent app."""
from fastapi import FastAPI, HTTPException
from .foundation import install_foundations, check_security_ready
from pydantic import BaseModel, Field

from .config import get_settings
from .providers import ProviderError
from .workflow import graph

app = FastAPI(title="__PROJECT_NAME__", version="0.2.0")
install_foundations(app)


class InvokeRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class InvokeResponse(BaseModel):
    answer: str
    tool_used: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    """Check local configuration; no billable or network provider probes."""
    try:
        get_settings()
        check_security_ready()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="Invalid local configuration") from exc
    return {"status": "ready"}


@app.get("/provider-status")
def provider_status() -> dict[str, str]:
    """Provider connectivity is unverified; readiness never incurs inference cost."""
    try:
        settings = get_settings()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="Invalid local configuration") from exc
    return {"provider": settings.provider, "connectivity": "not_checked"}


@app.post("/invoke", response_model=InvokeResponse)
def invoke(request: InvokeRequest) -> InvokeResponse:
    try:
        result = graph.invoke({"question": request.question, "answer": ""})
    except ProviderError as exc:
        raise HTTPException(
            status_code=503,
            detail="Configured inference provider is unavailable.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="Invalid local configuration") from exc
    return InvokeResponse(answer=result["answer"], tool_used=result.get("tool_used"))
