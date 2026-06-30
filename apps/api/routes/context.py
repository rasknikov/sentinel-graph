from fastapi import APIRouter, Depends

from packages.security.dependencies import require_tenant_context
from packages.security.tenant_context import TenantContext


router = APIRouter(tags=["context"])


@router.get("/me/context")
async def get_current_tenant_context(
    tenant_context: TenantContext = Depends(require_tenant_context),
) -> dict[str, object]:
    return {
        "tenant_id": tenant_context.tenant_id,
        "user_id": tenant_context.user_id,
        "roles": list(tenant_context.roles),
        "scopes": list(tenant_context.scopes),
        "department": tenant_context.department,
        "clearance_level": tenant_context.clearance_level,
        "session_id": tenant_context.session_id,
        "request_id": tenant_context.request_id,
        "trace_id": tenant_context.trace_id,
        "environment": tenant_context.environment,
        "auth_provider": tenant_context.auth_provider,
    }
