from pydantic import BaseModel, ConfigDict

from packages.common.ids import RequestId, TenantId, TraceId, UserId


class RequestIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    tenant_id: TenantId
    user_id: UserId
    request_id: RequestId
    trace_id: TraceId
