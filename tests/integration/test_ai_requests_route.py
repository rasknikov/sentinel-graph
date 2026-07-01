import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app
from packages.rag.citations import Citation
from packages.rag.dependencies import get_rag_orchestrator
from packages.rag.orchestrator import GroundedAnswerResult
from tests.integration.test_health_route import build_auth_header


class FakeRAGOrchestrator:
    async def answer(
        self,
        *,
        tenant_context,
        query_text: str,
        top_k: int = 5,
        filters=None,
    ) -> GroundedAnswerResult:
        return GroundedAnswerResult(
            answer="According to the active credit policy, analysts must follow the approved steps.",
            citations=(
                Citation(
                    document_id="doc_policy_v1",
                    document_version="v1",
                    chunk_id="chunk_1",
                    source="doc_policy_v1",
                    confidence=0.9,
                ),
            ),
            trace_id=tenant_context.trace_id,
            requires_human_review=False,
        )


@pytest.mark.asyncio
async def test_ai_requests_route_requires_authentication() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/v1/ai/requests",
            json={
                "mode": "rag_agent",
                "query_text": "What does the credit policy say?",
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
async def test_ai_requests_route_rejects_unsupported_mode() -> None:
    app.dependency_overrides[get_rag_orchestrator] = lambda: FakeRAGOrchestrator()
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/v1/ai/requests",
                headers=build_auth_header(),
                json={
                    "mode": "chat",
                    "query_text": "What does the credit policy say?",
                    "top_k": 5,
                    "filters": {},
                },
            )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()

    assert response.status_code == 400
    assert payload["error"]["code"] == "OUTPUT_VALIDATION_FAILED"
    assert payload["error"]["message"] == "Unsupported AI request mode."
    assert payload["error"]["trace_id"].startswith("trace_")


@pytest.mark.asyncio
async def test_ai_requests_route_returns_grounded_answer() -> None:
    app.dependency_overrides[get_rag_orchestrator] = lambda: FakeRAGOrchestrator()
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/v1/ai/requests",
                headers=build_auth_header(),
                json={
                    "mode": "rag_agent",
                    "query_text": "What does the credit policy say?",
                    "top_k": 5,
                    "filters": {},
                },
            )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()

    assert response.status_code == 200
    assert payload["request_id"].startswith("req_")
    assert payload["trace_id"].startswith("trace_")
    assert payload["status"] == "completed"
    assert payload["answer"].startswith("According to the active credit policy")
    assert payload["citations"][0]["document_id"] == "doc_policy_v1"
    assert payload["citations"][0]["document_version"] == "v1"
    assert payload["citations"][0]["chunk_id"] == "chunk_1"
    assert payload["requires_human_review"] is False
