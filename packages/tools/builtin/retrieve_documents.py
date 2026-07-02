from packages.rag.contracts import RetrievalFilters, RetrievalRequest
from packages.rag.vector_access_gateway import VectorAccessGateway
from packages.security.tenant_context import TenantContext
from packages.tools.schemas import ToolResult


class RetrieveDocumentsTool:
    def __init__(
        self,
        vector_access_gateway: VectorAccessGateway,
    ) -> None:
        self._vector_access_gateway = vector_access_gateway

    async def __call__(
        self,
        tenant_context: TenantContext,
        arguments: dict,
    ) -> ToolResult:
        query_text = str(arguments.get("query_text", "")).strip()
        top_k = int(arguments.get("top_k", 5))
        filters = RetrievalFilters(
            document_id=arguments.get("document_id"),
            version=arguments.get("version"),
            classification=arguments.get("classification"),
        )

        retrieval_result = await self._vector_access_gateway.search(
            RetrievalRequest(
                tenant_context=tenant_context,
                query_text=query_text,
                top_k=top_k,
                filters=filters,
            )
        )

        return ToolResult(
            tool_name="retrieve_documents",
            tool_version="v1",
            success=True,
            data={
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
                    for chunk in retrieval_result.chunks
                )
            },
            metadata={
                "retrieved_count": len(retrieval_result.chunks),
            },
        )