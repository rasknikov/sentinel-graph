from packages.common.errors import ErrorCode
from packages.governance.policy.contracts import (
    PolicyCheck,
    PolicyDecisionType,
)
from packages.governance.policy.engine import PolicyEngine
from packages.security.tenant_context import TenantContext


def build_tenant_context(*, scopes: tuple[str, ...]) -> TenantContext:
    return TenantContext(
        tenant_id="tenant_credit",
        user_id="user_123",
        roles=("analyst",),
        scopes=scopes,
        department="credit",
        clearance_level="internal",
        session_id="session_abc",
        request_id="req_123",
        trace_id="trace_123",
        environment="test",
        auth_provider="https://identity.example.com",
    )


def test_policy_engine_denies_without_tenant_context() -> None:
    engine = PolicyEngine()

    decision = engine.evaluate(
        tenant_context=None,
        check=PolicyCheck(
            action="read:self_policy_check",
            required_scopes=("rag:query",),
        ),
    )

    assert decision.decision is PolicyDecisionType.DENY
    assert decision.reason == "Tenant context is required."
    assert decision.error_code is ErrorCode.TENANT_CONTEXT_MISSING


def test_policy_engine_denies_when_scope_is_missing() -> None:
    engine = PolicyEngine()
    tenant_context = build_tenant_context(scopes=("documents:read",))

    decision = engine.evaluate(
        tenant_context=tenant_context,
        check=PolicyCheck(
            action="read:self_policy_check",
            required_scopes=("rag:query",),
        ),
    )

    assert decision.decision is PolicyDecisionType.DENY
    assert decision.reason == "Required scope is missing."
    assert decision.error_code is ErrorCode.TENANT_ACCESS_DENIED
    assert decision.trace_id == "trace_123"


def test_policy_engine_allows_when_scope_is_present() -> None:
    engine = PolicyEngine()
    tenant_context = build_tenant_context(scopes=("rag:query",))

    decision = engine.evaluate(
        tenant_context=tenant_context,
        check=PolicyCheck(
            action="read:self_policy_check",
            required_scopes=("rag:query",),
        ),
    )

    assert decision.decision is PolicyDecisionType.ALLOW
    assert decision.reason == "Policy check passed."
    assert decision.error_code is None
    assert decision.request_id == "req_123"
