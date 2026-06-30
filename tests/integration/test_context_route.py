import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt

from apps.api.main import app
from packages.common.config import settings
from tests.integration.test_health_route import build_auth_header


@pytest.mark.asyncio
async def test_context_route_requires_authentication() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/me/context")

    payload = response.json()

    assert response.status_code == 401
    assert payload["code"] == "authentication_required"
    assert payload["message"] == "Authentication is required."
    assert payload["trace_id"].startswith("trace_")


@pytest.mark.asyncio
async def test_context_route_returns_current_tenant_context() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/me/context", headers=build_auth_header())

    payload = response.json()

    assert response.status_code == 200
    assert payload["tenant_id"] == "tenant_credit"
    assert payload["user_id"] == "user_123"
    assert payload["roles"] == ["analyst"]
    assert payload["scopes"] == ["rag:query"]
    assert payload["department"] == "credit"
    assert payload["clearance_level"] == "internal"
    assert payload["session_id"] == "session_abc"
    assert payload["request_id"].startswith("req_")
    assert payload["trace_id"].startswith("trace_")
    assert payload["environment"] == "development"
    assert payload["auth_provider"] == "https://identity.example.com"


@pytest.mark.asyncio
async def test_context_route_rejects_malformed_token() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/me/context",
            headers={"Authorization": "Bearer not-a-real-jwt"},
        )

    payload = response.json()

    assert response.status_code == 401
    assert payload["code"] == "invalid_authentication"
    assert payload["message"] == "Authentication is invalid."
    assert payload["trace_id"].startswith("trace_")


@pytest.mark.asyncio
async def test_context_route_rejects_token_with_invalid_signature() -> None:
    token = jwt.encode(
        {
            "sub": "user_123",
            "tenant_id": "tenant_credit",
            "session_id": "session_abc",
            "roles": ["analyst"],
            "scopes": ["rag:query"],
            "department": "credit",
            "clearance_level": "internal",
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
        },
        "wrong-secret",
        algorithm=settings.jwt_algorithm,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/me/context",
            headers={"Authorization": f"Bearer {token}"},
        )

    payload = response.json()

    assert response.status_code == 401
    assert payload["code"] == "invalid_authentication"
    assert payload["message"] == "Authentication is invalid."
    assert payload["trace_id"].startswith("trace_")


@pytest.mark.asyncio
async def test_context_route_rejects_token_with_missing_required_claim() -> None:
    token = jwt.encode(
        {
            "sub": "user_123",
            "tenant_id": "tenant_credit",
            "roles": ["analyst"],
            "scopes": ["rag:query"],
            "department": "credit",
            "clearance_level": "internal",
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/me/context",
            headers={"Authorization": f"Bearer {token}"},
        )

    payload = response.json()

    assert response.status_code == 401
    assert payload["code"] == "invalid_authentication"
    assert payload["message"] == "Authentication is invalid."
    assert payload["trace_id"].startswith("trace_")


@pytest.mark.asyncio
async def test_context_route_rejects_token_with_invalid_issuer() -> None:
    token = jwt.encode(
        {
            "sub": "user_123",
            "tenant_id": "tenant_credit",
            "session_id": "session_abc",
            "roles": ["analyst"],
            "scopes": ["rag:query"],
            "department": "credit",
            "clearance_level": "internal",
            "iss": "https://wrong-issuer.example.com",
            "aud": settings.jwt_audience,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/me/context",
            headers={"Authorization": f"Bearer {token}"},
        )

    payload = response.json()

    assert response.status_code == 401
    assert payload["code"] == "invalid_authentication"
    assert payload["message"] == "Authentication is invalid."
    assert payload["trace_id"].startswith("trace_")


@pytest.mark.asyncio
async def test_context_route_rejects_token_with_invalid_audience() -> None:
    token = jwt.encode(
        {
            "sub": "user_123",
            "tenant_id": "tenant_credit",
            "session_id": "session_abc",
            "roles": ["analyst"],
            "scopes": ["rag:query"],
            "department": "credit",
            "clearance_level": "internal",
            "iss": settings.jwt_issuer,
            "aud": "wrong-audience",
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/me/context",
            headers={"Authorization": f"Bearer {token}"},
        )

    payload = response.json()

    assert response.status_code == 401
    assert payload["code"] == "invalid_authentication"
    assert payload["message"] == "Authentication is invalid."
    assert payload["trace_id"].startswith("trace_")
