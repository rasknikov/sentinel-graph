import pytest

from packages.ai_gateway.contracts import EmbeddingRequest, EmbeddingResult
from packages.ingestion.contracts import (
    DocumentRegistrationRequest,
    DocumentStatus,
    DocumentVersionRecord,
)
from packages.ingestion.pipeline import (
    DEFAULT_EMBEDDING_MODEL_NAME,
    DocumentIngestionPipeline,
)
from packages.security.tenant_context import TenantContext


def build_tenant_context() -> TenantContext:
    return TenantContext(
        tenant_id="tenant_credit",
        user_id="user_123",
        roles=("analyst",),
        scopes=("documents:write",),
        department="credit",
        clearance_level="internal",
        session_id="session_abc",
        request_id="req_123",
        trace_id="trace_123",
        environment="test",
        auth_provider="https://identity.example.com",
    )


class FakeAIGatewayService:
    def __init__(self) -> None:
        self.requests: list[EmbeddingRequest] = []

    async def generate_embedding(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResult:
        self.requests.append(request)
        return EmbeddingResult(
            model_name=request.model_name,
            embedding=[0.1, 0.2, 0.3],
        )


@pytest.mark.asyncio
async def test_pipeline_generates_chunks_and_calls_ai_gateway_for_embeddings() -> None:
    ai_gateway_service = FakeAIGatewayService()
    pipeline = DocumentIngestionPipeline(ai_gateway_service=ai_gateway_service)
    request = DocumentRegistrationRequest(
        tenant_context=build_tenant_context(),
        document_id="doc_policy_v1",
        title="Credit Policy",
        source_system="sharepoint",
        content_text="abcdefghij",
        content_hash="hash_123",
        version="v1",
        classification="internal",
    )
    version_record = DocumentVersionRecord(
        document_id="doc_policy_v1",
        tenant_id="tenant_credit",
        created_by="user_123",
        version="v1",
        content_text="abcdefghij",
        content_hash="hash_123",
        classification="internal",
        status=DocumentStatus.DRAFT,
    )

    chunks, embedded_chunks = await pipeline.process_document(
        request=request,
        version_record=version_record,
    )

    assert chunks
    assert embedded_chunks
    assert len(ai_gateway_service.requests) == len(chunks)
    assert ai_gateway_service.requests[0].tenant_context.tenant_id == "tenant_credit"
    assert ai_gateway_service.requests[0].model_name == DEFAULT_EMBEDDING_MODEL_NAME
    assert embedded_chunks[0].chunk_id == chunks[0].chunk_id
    assert embedded_chunks[0].embedding_model_name == DEFAULT_EMBEDDING_MODEL_NAME
