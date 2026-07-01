import pytest

from packages.common.errors import DomainError, ErrorCode
from packages.rag.contracts import (
    RetrievedChunk,
    RetrievalFilters,
    RetrievalRequest,
    RetrievalResult,
)
from packages.rag.vector_access_gateway import VectorAccessGateway
from packages.security.tenant_context import TenantContext


def build_tenant_context() -> TenantContext:
    return TenantContext(
        tenant_id="tenant_credit",
        user_id="user_123",
        roles=("analyst",),
        scopes=("rag:query",),
        department="credit",
        clearance_level="internal",
        session_id="session_abc",
        request_id="req_123",
        trace_id="trace_123",
        environment="test",
        auth_provider="https://identity.example.com",
    )


class FakeDocumentChunkRetriever:
    def __init__(self) -> None:
        self.last_request: dict[str, object] | None = None

    async def search(
        self,
        *,
        tenant_context: TenantContext,
        query_text: str,
        top_k: int,
        filters: RetrievalFilters,
    ) -> RetrievalResult:
        self.last_request = {
            "tenant_context": tenant_context,
            "query_text": query_text,
            "top_k": top_k,
            "filters": filters,
        }
        return RetrievalResult(
            chunks=(
                RetrievedChunk(
                    chunk_id="chunk_1",
                    document_id="doc_policy_v1",
                    version="v1",
                    tenant_id=tenant_context.tenant_id,
                    content_text="Credit policy content",
                    classification="internal",
                    score=1.0,
                ),
            )
        )


@pytest.mark.asyncio
async def test_search_rejects_blank_query_text() -> None:
    gateway = VectorAccessGateway(retriever=FakeDocumentChunkRetriever())

    with pytest.raises(DomainError) as exc_info:
        await gateway.search(
            RetrievalRequest(
                tenant_context=build_tenant_context(),
                query_text="   ",
                top_k=5,
                filters=RetrievalFilters(),
            )
        )

    assert exc_info.value.code is ErrorCode.OUTPUT_VALIDATION_FAILED
    assert exc_info.value.message == "Query text is required."
    assert exc_info.value.trace_id == "trace_123"


@pytest.mark.asyncio
async def test_search_rejects_non_positive_top_k() -> None:
    gateway = VectorAccessGateway(retriever=FakeDocumentChunkRetriever())

    with pytest.raises(DomainError) as exc_info:
        await gateway.search(
            RetrievalRequest(
                tenant_context=build_tenant_context(),
                query_text="credit policy",
                top_k=0,
                filters=RetrievalFilters(),
            )
        )

    assert exc_info.value.code is ErrorCode.OUTPUT_VALIDATION_FAILED
    assert exc_info.value.message == "top_k must be greater than zero."
    assert exc_info.value.trace_id == "trace_123"


@pytest.mark.asyncio
async def test_search_delegates_to_retriever_for_valid_request() -> None:
    retriever = FakeDocumentChunkRetriever()
    gateway = VectorAccessGateway(retriever=retriever)

    result = await gateway.search(
        RetrievalRequest(
            tenant_context=build_tenant_context(),
            query_text="credit policy",
            top_k=5,
            filters=RetrievalFilters(
                classification="internal",
            ),
        )
    )

    assert retriever.last_request is not None
    assert retriever.last_request["tenant_context"].tenant_id == "tenant_credit"
    assert retriever.last_request["query_text"] == "credit policy"
    assert retriever.last_request["top_k"] == 5
    assert result.chunks[0].chunk_id == "chunk_1"
    assert result.chunks[0].tenant_id == "tenant_credit"
