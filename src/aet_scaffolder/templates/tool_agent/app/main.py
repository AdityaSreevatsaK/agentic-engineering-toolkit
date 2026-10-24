"""HTTP interface for the generated agent app."""
from fastapi import FastAPI
from pydantic import BaseModel, Field

from .workflow import graph

app = FastAPI(title="__PROJECT_NAME__", version="0.1.0")


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
    result = graph.invoke({"question": request.question, "answer": ""})
    return InvokeResponse(answer=result["answer"], tool_used=result.get("tool_used"))
