from packages.common.errors import DomainError, ErrorCode
from packages.rag.contracts import RetrievalRequest, RetrievalResult
from packages.rag.retriever import DocumentChunkRetriever


class VectorAccessGateway:
    def __init__(
        self,
        retriever: DocumentChunkRetriever,
    ) -> None:
        self._retriever = retriever

    async def search(
        self,
        request: RetrievalRequest,
    ) -> RetrievalResult:
        if request.tenant_context is None:
            raise DomainError(
                code=ErrorCode.TENANT_CONTEXT_MISSING,
                message="Tenant context is required.",
                trace_id="trace_unknown",
            )

        if not request.query_text.strip():
            raise DomainError(
                code=ErrorCode.OUTPUT_VALIDATION_FAILED,
                message="Query text is required.",
                trace_id=request.tenant_context.trace_id,
            )

        if request.top_k <= 0:
            raise DomainError(
                code=ErrorCode.OUTPUT_VALIDATION_FAILED,
                message="top_k must be greater than zero.",
                trace_id=request.tenant_context.trace_id,
            )

        return await self._retriever.search(
            tenant_context=request.tenant_context,
            query_text=request.query_text,
            top_k=request.top_k,
            filters=request.filters,
        )