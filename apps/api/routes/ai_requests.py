from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from packages.common.errors import DomainError, ErrorCode
from packages.rag.contracts import RetrievalFilters
from packages.rag.dependencies import get_rag_orchestrator
from packages.rag.orchestrator import RAGOrchestrator
from packages.security.dependencies import require_tenant_context
from packages.security.tenant_context import TenantContext


router = APIRouter(tags=["ai-requests"])


class AIRequestPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    mode: str
    query_text: str
    top_k: int = 5
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)


@router.post("/v1/ai/requests")
async def create_ai_request(
    payload: AIRequestPayload,
    tenant_context: TenantContext = Depends(require_tenant_context),
    rag_orchestrator: RAGOrchestrator = Depends(get_rag_orchestrator),
) -> dict[str, object]:
    if payload.mode != "rag_agent":
        raise DomainError(
            code=ErrorCode.OUTPUT_VALIDATION_FAILED,
            message="Unsupported AI request mode.",
            trace_id=tenant_context.trace_id,
        )

    result = await rag_orchestrator.answer(
        tenant_context=tenant_context,
        query_text=payload.query_text,
        top_k=payload.top_k,
        filters=payload.filters,
    )

    return {
        "request_id": tenant_context.request_id,
        "trace_id": result.trace_id,
        "status": "completed",
        "answer": result.answer,
        "citations": tuple(
            {
                "document_id": citation.document_id,
                "document_version": citation.document_version,
                "chunk_id": citation.chunk_id,
                "source": citation.source,
                "confidence": citation.confidence,
            }
            for citation in result.citations
        ),
        "requires_human_review": result.requires_human_review,
    }
