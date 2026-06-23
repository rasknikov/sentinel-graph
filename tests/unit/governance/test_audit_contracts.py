from packages.governance.audit import AuditRecordRef
from packages.common.errors import ErrorCode
from packages.common.ids import AuditId, RequestId, TenantId, TraceId, UserId


def test_audit_contract_reuses_common_ids_and_error_codes() -> None:
    record = AuditRecordRef(
        audit_id=AuditId("audit_123"),
        tenant_id=TenantId("tenant_credit"),
        user_id=UserId("user_123"),
        request_id=RequestId("req_123"),
        trace_id=TraceId("trace_123"),
        event_type="policy_denied",
        error_code=ErrorCode.POLICY_DENIED,
    )

    assert record.model_dump(mode="json") == {
        "audit_id": "audit_123",
        "tenant_id": "tenant_credit",
        "user_id": "user_123",
        "request_id": "req_123",
        "trace_id": "trace_123",
        "event_type": "policy_denied",
        "error_code": "POLICY_DENIED",
    }
