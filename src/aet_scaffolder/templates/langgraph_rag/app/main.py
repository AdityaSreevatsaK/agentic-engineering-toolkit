"""Local-only FastAPI entry point. This demo has no authentication."""
from unicodedata import normalize

from fastapi import FastAPI, HTTPException, Request
from .foundation import install_foundations, check_security_ready, tenant_knowledge_path
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .config import get_settings
from .knowledge import KnowledgeError, load_documents
from .providers import ProviderError
from .workflow import graph

app = FastAPI(title="__PROJECT_NAME__", version="0.1.0")
install_foundations(app)


class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question", mode="before")
    @classmethod
    def normalise_question(cls, value: object) -> object:
        """Normalise Unicode, reject controls, and preserve query semantics."""
        if not isinstance(value, str):
            return value
        # Leave oversized values to the existing Field length validator.
        if len(value) > 2000:
            return value
        question = normalize("NFKC", value).strip()
        if any(((ord(char) < 32 and ord(char) not in (9, 10, 13))
                or ord(char) == 127) for char in question):
            raise ValueError("Question contains invalid control characters")
        return question


class QueryResponse(BaseModel):
    answer: str
    source_ids: list[str]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    """Local readiness only: validate settings and tenant corpora, not cloud access."""
    try:
        settings = get_settings()
        tenants = check_security_ready()
        if tenants:
            for tenant in tenants:
                load_documents(tenant_knowledge_path(settings.knowledge_path, tenant))
        else:
            load_documents(settings.knowledge_path)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=503, detail="Local RAG readiness unavailable") from exc
    return {"status": "ready"}


@app.get("/provider-status")
def provider_status() -> dict[str, str]:
    """Provider connectivity is unverified; readiness never incurs inference cost."""
    try:
        settings = get_settings()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="Invalid local configuration") from exc
    return {"provider": settings.provider, "connectivity": "not_checked"}


@app.post("/ask", response_model=QueryResponse)
def ask(request: QueryRequest, http_request: Request) -> QueryResponse:
    try:
        settings = get_settings()
        knowledge_path = tenant_knowledge_path(
            settings.knowledge_path, getattr(http_request.state, "tenant_id", None)
        )
        result = graph.invoke({"question": request.question, "knowledge_path": knowledge_path})
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
