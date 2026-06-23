from fastapi.testclient import TestClient

from apps.api.main import create_app
from packages.common.errors import DomainError, ErrorCode


def test_health_endpoint_works() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_domain_error_handler_returns_documented_shape() -> None:
    app = create_app()

    @app.get("/boom")
    async def boom() -> None:
        raise DomainError(
            code=ErrorCode.POLICY_DENIED,
            message="This request cannot be completed in the current context.",
            trace_id="trace_321",
            details={"internal_reason": "policy rule x"},
        )

    client = TestClient(app)
    response = client.get("/boom")

    assert response.status_code == 403
    assert response.json() == {
        "error": {
            "code": "POLICY_DENIED",
            "message": "This request cannot be completed in the current context.",
            "trace_id": "trace_321",
        }
    }
