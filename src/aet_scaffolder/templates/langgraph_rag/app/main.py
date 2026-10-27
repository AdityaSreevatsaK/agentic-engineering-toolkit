"""Local-only FastAPI entry point. This demo has no authentication."""
from fastapi import FastAPI, HTTPException
from .foundation import install_foundations
from pydantic import BaseModel, Field

from .config import get_settings
from .knowledge import KnowledgeError, load_documents
from .providers import ProviderError
from .workflow import graph

app = FastAPI(title="__PROJECT_NAME__", version="0.1.0")
install_foundations(app)


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class QueryResponse(BaseModel):
    answer: str
    source_ids: list[str]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    """Validate mock configuration and corpus; never probes an external model."""
    try:
        settings = get_settings()
        if settings.provider != "mock":
            raise HTTPException(status_code=503, detail="Live model readiness has not been verified")
        load_documents(settings.knowledge_path)
    except HTTPException:
        raise
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=503, detail="Local RAG readiness unavailable") from exc
    return {"status": "ready"}


@app.post("/ask", response_model=QueryResponse)
def ask(request: QueryRequest) -> QueryResponse:
    try:
        result = graph.invoke({"question": request.question})
    except KnowledgeError as exc:
        raise HTTPException(status_code=503, detail="Local knowledge base unavailable") from exc
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail="Configured inference provider is unavailable") from exc
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="Invalid local configuration") from exc
    return QueryResponse(
        answer=result["answer"],
        source_ids=[source["id"] for source in result.get("sources", [])],
    )
