from fastapi import Request

from packages.common.errors import DomainError, ErrorCode
from packages.security.tenant_context import TenantContext


def require_tenant_context(request: Request) -> TenantContext:
    tenant_context = getattr(request.state, "tenant_context", None)
    trace_id = getattr(request.state, "trace_id", "trace_unknown")

    if tenant_context is None:
        raise DomainError(
            code=ErrorCode.TENANT_CONTEXT_MISSING,
            message="Tenant context is required.",
            trace_id=trace_id,
        )
    
    return tenant_context