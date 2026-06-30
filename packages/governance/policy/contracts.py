from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from packages.common.errors import ErrorCode
from packages.common.ids import RequestId, TenantId, TraceId, UserId


class PolicyDecisionType(StrEnum):
    ALLOW = "allow"
    DENY = "deny"


class PolicyDecision(BaseModel):
    model_config = ConfigDict(fronze=True)

    decision: PolicyDecisionType
    reason: str
    trace_id: TraceId
    request_id: RequestId
    tenant_id: TenantId
    user_id: UserId
    error_code: ErrorCode | None = None


class PolicyCheck(BaseModel):
    model_config = ConfigDict(frozen=True)

    action: str
    required_scopes: tuple[str, ...] = ()
    resource_id: str | None = None