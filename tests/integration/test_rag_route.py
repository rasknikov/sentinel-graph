import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app
from packages.ai_gateway.contracts import EmbeddingRequest, EmbeddingResult
from packages.ai_gateway.dependencies import get_ai_gateway_service
from packages.common.db.dependencies import get_db_session
from tests.integration.test_health_route import build_auth_header
from tests.integration.test_rag_retriever import seed_retrieval_records


def build_db_session_override(db_session):
    async def _override_db_session():
        yield db_session

    return _override_db_session


class FakeAIGatewayService:
    async def generate_embedding(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResult:
        return EmbeddingResult(
            model_name=request.model_name,
            embedding=[0.1, 0.2, 0.3],
        )


@pytest.mark.asyncio
async def test_rag_search_route_requires_authentication() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/v1/rag/search",
            json={
                "query_text": "credit policy",
                "top_k": 5,
                "filters": {},
            },
        )

    payload = response.json()

    assert response.status_code == 401
    assert payload["code"] == "authentication_required"
    assert payload["message"] == "Authentication is required."
    assert payload["trace_id"].startswith("trace_")


@pytest.mark.asyncio
async def test_rag_search_route_returns_active_chunks_for_current_tenant(db_session) -> None:
    await seed_retrieval_records(db_session)
    app.dependency_overrides[get_db_session] = build_db_session_override(db_session)
    app.dependency_overrides[get_ai_gateway_service] = lambda: FakeAIGatewayService()
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/v1/rag/search",
                headers=build_auth_header(),
                json={
                    "query_text": "credit policy",
                    "top_k": 5,
                    "filters": {},
                },
            )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()

    assert response.status_code == 200
    assert len(payload["chunks"]) == 1
    assert payload["chunks"][0]["chunk_id"] == "chunk_credit_1"
    assert payload["chunks"][0]["tenant_id"] == "tenant_credit"
    assert payload["chunks"][0]["document_id"] == "doc_policy_active"


@pytest.mark.asyncio
async def test_rag_search_route_respects_filters_and_excludes_other_tenants(db_session) -> None:
    await seed_retrieval_records(db_session)
    app.dependency_overrides[get_db_session] = build_db_session_override(db_session)
    app.dependency_overrides[get_ai_gateway_service] = lambda: FakeAIGatewayService()
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/v1/rag/search",
                headers=build_auth_header(),
                json={
                    "query_text": "policy",
                    "top_k": 5,
                    "filters": {
                        "document_id": "doc_policy_active",
                        "version": "v1",
                        "classification": "internal",
                    },
                },
            )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()

    assert response.status_code == 200
    assert len(payload["chunks"]) == 1
    assert payload["chunks"][0]["document_id"] == "doc_policy_active"
    assert payload["chunks"][0]["version"] == "v1"
    assert payload["chunks"][0]["classification"] == "internal"
    assert payload["chunks"][0]["tenant_id"] == "tenant_credit"
