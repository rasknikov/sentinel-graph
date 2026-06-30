from fastapi import APIRouter, Depends

from packages.governance.policy.contracts import PolicyCheck
from packages.governance.policy.dependencies import get_policy_engine
from packages.governance.policy.engine import PolicyEngine
from packages.security.dependencies import require_tenant_context
from packages.security.tenant_context import TenantContext


router = APIRouter(tags=["policy"])


@router.get("/me/policy-check")
async def check_current_policy(
    tenant_context: TenantContext = Depends(require_tenant_context),
    policy_engine: PolicyEngine = Depends(get_policy_engine),
) -> dict[str, object]:
    check = PolicyCheck(
        action="read:self_policy_check",
        required_scopes=("rag:query",),
    )

    decision = policy_engine.evaluate(
        tenant_context=tenant_context,
        check=check,
    )

    return {
        "decision": decision.decision,
        "reason": decision.reason,
        "trace_id": decision.trace_id,
        "request_id": decision.request_id,
        "tenant_id": decision.tenant_id,
        "user_id": decision.user_id,
        "error_code": decision.error_code,
    }
