import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt

from apps.api.main import app
from packages.common.config import settings
from tests.integration.test_health_route import build_auth_header


def build_auth_header_without_required_scope() -> dict[str, str]:
    token = jwt.encode(
        {
            "sub": "user_123",
            "tenant_id": "tenant_credit",
            "session_id": "session_abc",
            "roles": ["analyst"],
            "scopes": ["documents:read"],
            "department": "credit",
            "clearance_level": "internal",
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_policy_route_allows_request_with_required_scope() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/me/policy-check", headers=build_auth_header())

    payload = response.json()

    assert response.status_code == 200
    assert payload["decision"] == "allow"
    assert payload["reason"] == "Policy check passed."
    assert payload["trace_id"].startswith("trace_")
    assert payload["request_id"].startswith("req_")
    assert payload["tenant_id"] == "tenant_credit"
    assert payload["user_id"] == "user_123"
    assert payload["error_code"] is None


@pytest.mark.asyncio
async def test_policy_route_denies_request_without_required_scope() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/me/policy-check",
            headers=build_auth_header_without_required_scope(),
        )

    payload = response.json()

    assert response.status_code == 200
    assert payload["decision"] == "deny"
    assert payload["reason"] == "Required scope is missing."
    assert payload["trace_id"].startswith("trace_")
    assert payload["request_id"].startswith("req_")
    assert payload["tenant_id"] == "tenant_credit"
    assert payload["user_id"] == "user_123"
    assert payload["error_code"] == "TENANT_ACCESS_DENIED"
