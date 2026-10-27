"""HTTP interface for the generated local-first agent app."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .providers import ProviderError
from .workflow import graph

app = FastAPI(title="legacy-m10-agent", version="0.2.0")


class InvokeRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class InvokeResponse(BaseModel):
    answer: str
    tool_used: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/invoke", response_model=InvokeResponse)
def invoke(request: InvokeRequest) -> InvokeResponse:
    try:
        result = graph.invoke({"question": request.question, "answer": ""})
    except ProviderError as exc:
        raise HTTPException(
            status_code=503,
            detail="Local inference unavailable; ensure Ollama is running and the model is installed.",
        ) from exc
    return InvokeResponse(answer=result["answer"], tool_used=result.get("tool_used"))
