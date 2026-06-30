import pytest
from fastapi import Request

from packages.common.errors import DomainError, ErrorCode
from packages.security.dependencies import require_tenant_context
from packages.security.tenant_context import TenantContext


def build_request_with_state(**state_values: object) -> Request:
    scope = {"type": "http", "headers": [], "state": dict(state_values)}
    return Request(scope)


def test_require_tenant_context_returns_context_when_present() -> None:
    tenant_context = TenantContext(
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

    request = build_request_with_state(
        tenant_context=tenant_context,
        trace_id="trace_123",
    )

    assert require_tenant_context(request) is tenant_context


def test_require_tenant_context_fails_closed_when_missing() -> None:
    request = build_request_with_state(trace_id="trace_123")

    with pytest.raises(DomainError) as exc_info:
        require_tenant_context(request)

    assert exc_info.value.code is ErrorCode.TENANT_CONTEXT_MISSING
    assert exc_info.value.trace_id == "trace_123"
