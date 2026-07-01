import pytest

from packages.ai_gateway.contracts import EmbeddingRequest, EmbeddingResult
from packages.rag.contracts import RetrievalFilters
from packages.rag.semantic_retriever import SemanticDocumentChunkRetriever
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


class FakeScalarResult:
    def __init__(self, rows: list[object]) -> None:
        self._rows = rows

    def all(self) -> list[object]:
        return self._rows


class FakeExecuteResult:
    def __init__(self, rows: list[object]) -> None:
        self._rows = rows

    def scalars(self) -> FakeScalarResult:
        return FakeScalarResult(self._rows)


class FakeAsyncSession:
    def __init__(self, rows: list[object]) -> None:
        self.rows = rows
        self.last_statement = None

    async def execute(self, statement):
        self.last_statement = statement
        return FakeExecuteResult(self.rows)


class FakeChunkRow:
    def __init__(
        self,
        *,
        chunk_id: str,
        document_id: str,
        version: str,
        tenant_id: str,
        content_text: str,
        classification: str,
    ) -> None:
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.version = version
        self.tenant_id = tenant_id
        self.content_text = content_text
        self.classification = classification


@pytest.mark.asyncio
async def test_semantic_retriever_calls_ai_gateway_and_ranks_chunks() -> None:
    ai_gateway_service = FakeAIGatewayService()
    session = FakeAsyncSession(
        rows=[
            FakeChunkRow(
                chunk_id="chunk_1",
                document_id="doc_policy_v1",
                version="v1",
                tenant_id="tenant_credit",
                content_text="Credit policy for analysts.",
                classification="internal",
            ),
            FakeChunkRow(
                chunk_id="chunk_2",
                document_id="doc_policy_v1",
                version="v1",
                tenant_id="tenant_credit",
                content_text="Unrelated content.",
                classification="internal",
            ),
        ]
    )
    retriever = SemanticDocumentChunkRetriever(
        session=session,
        ai_gateway_service=ai_gateway_service,
    )

    result = await retriever.search(
        tenant_context=build_tenant_context(),
        query_text="credit policy",
        top_k=1,
        filters=RetrievalFilters(),
    )

    assert len(ai_gateway_service.requests) == 1
    assert ai_gateway_service.requests[0].tenant_context.tenant_id == "tenant_credit"
    assert ai_gateway_service.requests[0].model_name == "text-embedding-3-small"
    assert ai_gateway_service.requests[0].input_text == "credit policy"
    assert len(result.chunks) == 1
    assert result.chunks[0].chunk_id == "chunk_1"
    assert result.chunks[0].tenant_id == "tenant_credit"
