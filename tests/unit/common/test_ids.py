from packages.common.ids import CORE_ID_TYPES, RequestId, TenantId, TraceId


def test_core_id_types_cover_the_initial_contract_set() -> None:
    assert CORE_ID_TYPES == (
        "TenantId",
        "UserId",
        "SessionId",
        "RequestId",
        "TraceId",
        "DocumentId",
        "ChunkId",
        "PromptId",
        "ModelId",
        "ToolId",
        "PolicyId",
        "AuditId",
    )


def test_new_types_remain_string_compatible_at_runtime() -> None:
    tenant_id = TenantId("tenant_credit")
    request_id = RequestId("req_123")
    trace_id = TraceId("trace_789")

    assert isinstance(tenant_id, str)
    assert isinstance(request_id, str)
    assert isinstance(trace_id, str)
