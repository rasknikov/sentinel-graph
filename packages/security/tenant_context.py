from pydantic import BaseModel, ConfigDict

from packages.common.ids import RequestId, SessionId, TenantId, TraceId, UserId


class TenantContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    tenant_id: TenantId
    user_id: UserId
    roles: tuple[str, ...]
    scopes: tuple[str, ...]
    department: str
    clearance_level: str
    session_id: SessionId
    request_id: RequestId
    trace_id: TraceId
    environment: str
    auth_provider: str
