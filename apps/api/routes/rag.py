from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from packages.rag.contracts import RetrievalFilters, RetrievalRequest
from packages.rag.dependencies import get_vector_access_gateway
from packages.rag.vector_access_gateway import VectorAccessGateway
from packages.security.dependencies import require_tenant_context
from packages.security.tenant_context import TenantContext


router = APIRouter(tags=["rag"])


class SearchRequestPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    query_text: str
    top_k: int = 5
    filters: RetrievalFilters = RetrievalFilters()


@router.post("/v1/rag/search")
async def search_rag(
    payload: SearchRequestPayload,
    tenant_context: TenantContext = Depends(require_tenant_context),
    vector_access_gateway: VectorAccessGateway = Depends(get_vector_access_gateway),
) -> dict[str, tuple[dict[str, str | float], ...]]:
    result = await vector_access_gateway.search(
        RetrievalRequest(
            tenant_context=tenant_context,
            query_text=payload.query_text,
            top_k=payload.top_k,
            filters=payload.filters,
        )
    )

    return {
        "chunks": tuple(
            {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "version": chunk.version,
                "tenant_id": chunk.tenant_id,
                "content_text": chunk.content_text,
                "classification": chunk.classification,
                "score": chunk.score,
            }
            for chunk in result.chunks
        )
    }