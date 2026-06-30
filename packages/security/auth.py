from packages.common.config import settings
from packages.common.ids import RequestId, SessionId, TenantId, TraceId, UserId
from packages.security.jwt import TokenClaims
from packages.security.tenant_context import TenantContext


def build_tenant_context(
        claims: TokenClaims,
        request_id: RequestId,
        trace_id: TraceId,
) -> TenantContext:
    return TenantContext(
        tenant_id=TenantId(claims.tenant_id),
        user_id=UserId(claims.sub),
        roles=claims.roles,
        scopes=claims.scopes,
        department=claims.department,
        clearance_level=claims.clearance_level,
        session_id=SessionId(claims.session_id),
        request_id=request_id,
        trace_id=trace_id,
        environment=settings.environment,
        auth_provider=claims.iss,
    )
