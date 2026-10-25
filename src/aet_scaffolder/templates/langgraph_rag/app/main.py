"""Local-only FastAPI entry point. This demo has no authentication."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .knowledge import KnowledgeError
from .providers import ProviderError
from .workflow import graph

app = FastAPI(title="__PROJECT_NAME__", version="0.1.0")


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class QueryResponse(BaseModel):
    answer: str
    source_ids: list[str]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ask", response_model=QueryResponse)
def ask(request: QueryRequest) -> QueryResponse:
    try:
        result = graph.invoke({"question": request.question})
    except KnowledgeError as exc:
        raise HTTPException(status_code=503, detail="Local knowledge base unavailable") from exc
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail="Local Ollama inference unavailable") from exc
    return QueryResponse(
        answer=result["answer"],
        source_ids=[source["id"] for source in result.get("sources", [])],
    )
