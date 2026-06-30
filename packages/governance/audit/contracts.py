from pydantic import BaseModel, ConfigDict

from packages.common.errors import ErrorCode
from packages.common.ids import AuditId, RequestId, TenantId, TraceId, UserId


class AuditRecordRef(BaseModel):
    model_config = ConfigDict(frozen=True)

    audit_id: AuditId
    tenant_id: TenantId
    user_id: UserId
    request_id: RequestId
    trace_id: TraceId
    event_type: str
    error_code: ErrorCode | None = None


class AuditEventWrite(BaseModel):
    model_config = ConfigDict(frozen=True)

    tenant_id: TenantId
    user_id: UserId
    request_id: RequestId
    trace_id: TraceId
    event_type: str
    message: str
    error_code: ErrorCode | None = None