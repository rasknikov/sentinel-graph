from packages.common.errors import ErrorCode
from packages.governance.policy.contracts import(
    PolicyCheck,
    PolicyDecision,
    PolicyDecisionType,
)
from packages.security.tenant_context import TenantContext


class PolicyEngine:
    def evaluate(
            self,
            tenant_context: TenantContext | None,
            check: PolicyCheck,
    ) -> PolicyDecision:
        if tenant_context is None:
            return PolicyDecision(
                decision=PolicyDecisionType.DENY,
                reason="Tenant context is required.",
                trace_id="trace_unknown",
                request_id="req_unknown",
                tenant_id="tenant_unknown",
                user_id="user_unknown",
                error_code=ErrorCode.TENANT_CONTEXT_MISSING
            )
        
        missing_scopes = [
            scope for scope in check.required_scopes if scope not in tenant_context.scopes
        ]

        if missing_scopes:
            return PolicyDecision(
                decision=PolicyDecisionType.DENY,
                reason="Required scope is missing.",
                trace_id=tenant_context.trace_id,
                request_id=tenant_context.request_id,
                tenant_id=tenant_context.tenant_id,
                user_id=tenant_context.user_id,
                error_code=ErrorCode.TENANT_ACCESS_DENIED,
            )
        
        return PolicyDecision(
            decision=PolicyDecisionType.ALLOW,
            reason="Policy check passed.",
            trace_id=tenant_context.trace_id,
            request_id=tenant_context.request_id,
            tenant_id=tenant_context.tenant_id,
            user_id=tenant_context.user_id,
        )