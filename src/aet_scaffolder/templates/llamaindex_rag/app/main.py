"""Self-contained LlamaIndex RAG HTTP interface; never deploy unauthenticated."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .config import get_settings
from .foundation import install_foundations
from .knowledge import KnowledgeError, load_documents
from .providers import ProviderError, synthesise
from .retrieval import retrieve

app = FastAPI(title="__PROJECT_NAME__", version="0.1.0")
install_foundations(app)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class AskResponse(BaseModel):
    answer: str
    source_ids: list[str]


_NO_EVIDENCE = "No relevant passages were found in the local knowledge base."


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    """Check safe offline configuration and corpus only, not live credentials."""
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


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    try:
        settings = get_settings()
        hits = retrieve(
            request.question, load_documents(settings.knowledge_path), settings.top_k
        )
        sources = [{"id": hit.id, "text": hit.text} for hit in hits]
        if not sources:
            answer = _NO_EVIDENCE
        elif settings.provider == "mock":
            answer = f"Sample retrieved evidence [{hits[0].id}]: {hits[0].text}"
        else:
            answer = synthesise(request.question, sources, settings)
    except KnowledgeError as exc:
        raise HTTPException(status_code=503, detail="Local knowledge base unavailable") from exc
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail="Configured inference provider is unavailable") from exc
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="Invalid local configuration") from exc
    return AskResponse(answer=answer, source_ids=[source["id"] for source in sources])
