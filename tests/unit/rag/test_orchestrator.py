import pytest

from packages.ai_gateway.contracts import TextGenerationRequest, TextGenerationResult
from packages.common.errors import DomainError, ErrorCode
from packages.rag.contracts import (
    RetrievedChunk,
    RetrievalFilters,
    RetrievalRequest,
    RetrievalResult,
)
from packages.rag.orchestrator import RAGOrchestrator
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


class FakeVectorAccessGateway:
    def __init__(self, result: RetrievalResult) -> None:
        self.result = result
        self.last_request: RetrievalRequest | None = None

    async def search(
        self,
        request: RetrievalRequest,
    ) -> RetrievalResult:
        self.last_request = request
        return self.result


class FakeAIGatewayService:
    def __init__(self, output_text: str) -> None:
        self.output_text = output_text
        self.last_request: TextGenerationRequest | None = None

    async def generate_text(
        self,
        request: TextGenerationRequest,
    ) -> TextGenerationResult:
        self.last_request = request
        return TextGenerationResult(
            model_name=request.model_name,
            output_text=self.output_text,
        )


@pytest.mark.asyncio
async def test_orchestrator_returns_grounded_answer_with_citations() -> None:
    retrieval_result = RetrievalResult(
        chunks=(
            RetrievedChunk(
                chunk_id="chunk_1",
                document_id="doc_policy_v1",
                version="v1",
                tenant_id="tenant_credit",
                content_text="Credit policy for analysts.",
                classification="internal",
                score=0.9,
            ),
        )
    )
    vector_access_gateway = FakeVectorAccessGateway(result=retrieval_result)
    ai_gateway_service = FakeAIGatewayService(
        output_text="According to the active credit policy, analysts must follow the approved steps.",
    )
    orchestrator = RAGOrchestrator(
        vector_access_gateway=vector_access_gateway,
        ai_gateway_service=ai_gateway_service,
    )

    result = await orchestrator.answer(
        tenant_context=build_tenant_context(),
        query_text="What does the credit policy say?",
        top_k=3,
        filters=RetrievalFilters(classification="internal"),
    )

    assert vector_access_gateway.last_request is not None
    assert vector_access_gateway.last_request.tenant_context.tenant_id == "tenant_credit"
    assert vector_access_gateway.last_request.query_text == "What does the credit policy say?"
    assert ai_gateway_service.last_request is not None
    assert ai_gateway_service.last_request.model_name == "gpt-4.1-mini"
    assert "chunk_1" in ai_gateway_service.last_request.prompt
    assert result.answer.startswith("According to the active credit policy")
    assert result.citations[0].chunk_id == "chunk_1"
    assert result.citations[0].document_id == "doc_policy_v1"
    assert result.trace_id == "trace_123"
    assert result.requires_human_review is False


@pytest.mark.asyncio
async def test_orchestrator_fails_when_grounding_has_no_citations() -> None:
    vector_access_gateway = FakeVectorAccessGateway(
        result=RetrievalResult(chunks=())
    )
    ai_gateway_service = FakeAIGatewayService(
        output_text="I think the policy says analysts should proceed carefully.",
    )
    orchestrator = RAGOrchestrator(
        vector_access_gateway=vector_access_gateway,
        ai_gateway_service=ai_gateway_service,
    )

    with pytest.raises(DomainError) as exc_info:
        await orchestrator.answer(
            tenant_context=build_tenant_context(),
            query_text="What does the credit policy say?",
        )

    assert exc_info.value.code is ErrorCode.GROUNDING_FAILED
    assert exc_info.value.message == "Grounded answer requires citations."
    assert exc_info.value.trace_id == "trace_123"
