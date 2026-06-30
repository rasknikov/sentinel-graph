import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt

from apps.api.main import app
from packages.common.config import settings


def build_auth_header() -> dict[str, str]:
    token = jwt.encode(
        {
            "sub": "user_123",
            "tenant_id": "tenant_credit",
            "session_id": "session_abc",
            "roles": [" analyst ", "ANALYST"],
            "scopes": [" rag:query ", "RAG:QUERY"],
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
async def test_health_route_is_public() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_route_returns_ok_with_valid_token() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health", headers=build_auth_header())

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
