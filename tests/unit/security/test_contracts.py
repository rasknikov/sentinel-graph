from packages.security import RequestIdentity
from packages.common.ids import RequestId, TenantId, TraceId, UserId


def test_request_identity_reuses_common_id_contracts() -> None:
    identity = RequestIdentity(
        tenant_id=TenantId("tenant_credit"),
        user_id=UserId("user_123"),
        request_id=RequestId("req_123"),
        trace_id=TraceId("trace_123"),
    )

    assert identity.model_dump(mode="json") == {
        "tenant_id": "tenant_credit",
        "user_id": "user_123",
        "request_id": "req_123",
        "trace_id": "trace_123",
    }
