import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app
from packages.ai_gateway.contracts import (
    TextGenerationRequest,
    TextGenerationResult,
)
from packages.ai_gateway.dependencies import get_ai_gateway_service
from tests.integration.test_health_route import build_auth_header


class FakeAIGatewayService:
    async def generate_text(
        self,
        request: TextGenerationRequest,
    ) -> TextGenerationResult:
        return TextGenerationResult(
            model_name=request.model_name,
            output_text="SENTINEL",
        )


@pytest.mark.asyncio
async def test_ai_gateway_route_requires_authentication() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/me/generate-text")

    payload = response.json()

    assert response.status_code == 401
    assert payload["code"] == "authentication_required"
    assert payload["message"] == "Authentication is required."
    assert payload["trace_id"].startswith("trace_")


@pytest.mark.asyncio
async def test_ai_gateway_route_returns_generated_text() -> None:
    app.dependency_overrides[get_ai_gateway_service] = lambda: FakeAIGatewayService()
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/me/generate-text",
                headers=build_auth_header(),
            )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()

    assert response.status_code == 200
    assert payload == {
        "model_name": "gpt-4.1-mini",
        "output_text": "SENTINEL",
    }
