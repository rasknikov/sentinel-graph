from pydantic import BaseModel, ConfigDict, Field

from packages.security.tenant_context import TenantContext


class RetrievalFilters(BaseModel):
    model_config = ConfigDict(frozen=True)

    document_id: str | None = None
    version: str | None = None
    classification: str | None = None


class RetrievalRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    tenant_context: TenantContext
    query_text: str
    top_k: int = 5
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)


class RetrievedChunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    chunk_id: str
    document_id: str
    version: str
    tenant_id: str
    content_text: str
    classification: str
    score: float


class RetrievalResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    chunks: tuple[RetrievedChunk, ...]
