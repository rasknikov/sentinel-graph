import asyncio

import pytest

from packages.common.errors import DomainError, ErrorCode
from packages.governance.audit.contracts import AuditEventWrite
from packages.governance.policy.engine import PolicyEngine
from packages.rag.contracts import RetrievedChunk, RetrievalResult
from packages.security.tenant_context import TenantContext
from packages.tools.authorization import ToolAuthorizationService
from packages.tools.builtin import RetrieveDocumentsTool
from packages.tools.executor import ToolExecutor
from packages.tools.registry import ToolRegistry
from packages.tools.schemas import ToolDefinition, ToolProposal, ToolResult


def build_tenant_context() -> TenantContext:
    return TenantContext(
        tenant_id="tenant_credit",
        user_id="user_123",
        roles=("analyst",),
        scopes=("rag:query",),
        department="credit",
        clearance_level="internal",
        session_id="session_abc",
        request_id="req_123",
        trace_id="trace_123",
        environment="test",
        auth_provider="https://identity.example.com",
    )


class FakeVectorAccessGateway:
    def __init__(self) -> None:
        self.last_request = None

    async def search(self, request):
        self.last_request = request
        return RetrievalResult(
            chunks=(
                RetrievedChunk(
                    chunk_id="chunk_1",
                    document_id="doc_policy_v1",
                    version="v1",
                    tenant_id="tenant_credit",
                    content_text="Credit policy for analysts.",
                    classification="internal",
                    score=0.9,
                ),
            )
        )


class FakeAuditService:
    def __init__(self) -> None:
        self.events: list[AuditEventWrite] = []

    async def record_event(self, session, event: AuditEventWrite):
        self.events.append(event)
        return None


class SlowTool:
    async def __call__(self, tenant_context: TenantContext, arguments: dict) -> ToolResult:
        await asyncio.sleep(0.05)
        return ToolResult(
            tool_name="slow_tool",
            tool_version="v1",
            success=True,
        )


@pytest.mark.asyncio
async def test_tool_executor_executes_retrieve_documents_tool() -> None:
    vector_access_gateway = FakeVectorAccessGateway()
    audit_service = FakeAuditService()
    registry = ToolRegistry(
        definitions=(
            ToolDefinition(
                tool_id="tool_retrieve_documents_v1",
                name="retrieve_documents",
                version="v1",
                description="Retrieve authorized documents for the current tenant.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query_text": {"type": "string"},
                        "top_k": {"type": "integer"},
                        "classification": {"type": "string"},
                    },
                    "required": ["query_text"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "chunks": {"type": "array"},
                    },
                },
                risk_level="medium",
                allowed_tenants=("tenant_credit",),
                required_scopes=("rag:query",),
                requires_hitl=False,
                timeout_ms=5000,
                idempotent=True,
                status="active",
                audit_level="full",
            ),
        )
    )
    executor = ToolExecutor(
        registry=registry,
        authorization_service=ToolAuthorizationService(),
        policy_engine=PolicyEngine(),
        handlers={
            "retrieve_documents": RetrieveDocumentsTool(
                vector_access_gateway=vector_access_gateway,
            ),
        },
        audit_service=audit_service,
        session=object(),
    )

    result = await executor.execute(
        tenant_context=build_tenant_context(),
        proposal=ToolProposal(
            tool_name="retrieve_documents",
            tool_version="v1",
            arguments={
                "query_text": "credit policy",
                "top_k": 3,
                "classification": "internal",
            },
            reason="Need authorized retrieval for grounded answer.",
            risk_level="medium",
        ),
    )

    assert vector_access_gateway.last_request is not None
    assert vector_access_gateway.last_request.query_text == "credit policy"
    assert vector_access_gateway.last_request.top_k == 3
    assert vector_access_gateway.last_request.filters.classification == "internal"
    assert result.success is True
    assert result.tool_name == "retrieve_documents"
    assert result.tool_version == "v1"
    assert result.metadata["retrieved_count"] == 1
    assert result.data["chunks"][0]["document_id"] == "doc_policy_v1"
    assert [event.event_type for event in audit_service.events] == [
        "tool_call_proposed",
        "tool_executed",
    ]


@pytest.mark.asyncio
async def test_tool_executor_rejects_unknown_tool() -> None:
    executor = ToolExecutor(
        registry=ToolRegistry(definitions=()),
        authorization_service=ToolAuthorizationService(),
        policy_engine=PolicyEngine(),
        handlers={},
    )

    with pytest.raises(DomainError) as exc_info:
        await executor.execute(
            tenant_context=build_tenant_context(),
            proposal=ToolProposal(
                tool_name="unknown_tool",
                tool_version="v1",
                arguments={},
                reason="Need a tool.",
                risk_level="medium",
            ),
        )

    assert exc_info.value.code is ErrorCode.TOOL_NOT_FOUND


@pytest.mark.asyncio
async def test_tool_executor_rejects_inactive_tool() -> None:
    executor = ToolExecutor(
        registry=ToolRegistry(
            definitions=(
                ToolDefinition(
                    tool_id="tool_retrieve_documents_v1",
                    name="retrieve_documents",
                    version="v1",
                    description="Retrieve authorized documents for the current tenant.",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query_text": {"type": "string"},
                        },
                        "required": ["query_text"],
                    },
                    output_schema={"type": "object", "properties": {}},
                    risk_level="medium",
                    allowed_tenants=("tenant_credit",),
                    required_scopes=("rag:query",),
                    status="inactive",
                ),
            )
        ),
        authorization_service=ToolAuthorizationService(),
        policy_engine=PolicyEngine(),
        handlers={"retrieve_documents": RetrieveDocumentsTool(FakeVectorAccessGateway())},
    )

    with pytest.raises(DomainError) as exc_info:
        await executor.execute(
            tenant_context=build_tenant_context(),
            proposal=ToolProposal(
                tool_name="retrieve_documents",
                tool_version="v1",
                arguments={"query_text": "credit policy"},
                reason="Need a tool.",
                risk_level="medium",
            ),
        )

    assert exc_info.value.code is ErrorCode.TOOL_AUTHORIZATION_FAILED
    assert exc_info.value.message == "Requested tool is inactive."


@pytest.mark.asyncio
async def test_tool_executor_rejects_unauthorized_tenant() -> None:
    executor = ToolExecutor(
        registry=ToolRegistry(
            definitions=(
                ToolDefinition(
                    tool_id="tool_retrieve_documents_v1",
                    name="retrieve_documents",
                    version="v1",
                    description="Retrieve authorized documents for the current tenant.",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query_text": {"type": "string"},
                        },
                        "required": ["query_text"],
                    },
                    output_schema={"type": "object", "properties": {}},
                    risk_level="medium",
                    allowed_tenants=("tenant_compliance",),
                    required_scopes=("rag:query",),
                ),
            )
        ),
        authorization_service=ToolAuthorizationService(),
        policy_engine=PolicyEngine(),
        handlers={"retrieve_documents": RetrieveDocumentsTool(FakeVectorAccessGateway())},
    )

    with pytest.raises(DomainError) as exc_info:
        await executor.execute(
            tenant_context=build_tenant_context(),
            proposal=ToolProposal(
                tool_name="retrieve_documents",
                tool_version="v1",
                arguments={"query_text": "credit policy"},
                reason="Need a tool.",
                risk_level="medium",
            ),
        )

    assert exc_info.value.code is ErrorCode.TOOL_AUTHORIZATION_FAILED
    assert exc_info.value.message == "Tenant is not allowed to execute this tool."


@pytest.mark.asyncio
async def test_tool_executor_rejects_missing_scope() -> None:
    tenant_context = build_tenant_context().model_copy(update={"scopes": ("documents:read",)})
    executor = ToolExecutor(
        registry=ToolRegistry(
            definitions=(
                ToolDefinition(
                    tool_id="tool_retrieve_documents_v1",
                    name="retrieve_documents",
                    version="v1",
                    description="Retrieve authorized documents for the current tenant.",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query_text": {"type": "string"},
                        },
                        "required": ["query_text"],
                    },
                    output_schema={"type": "object", "properties": {}},
                    risk_level="medium",
                    allowed_tenants=("tenant_credit",),
                    required_scopes=("rag:query",),
                ),
            )
        ),
        authorization_service=ToolAuthorizationService(),
        policy_engine=PolicyEngine(),
        handlers={"retrieve_documents": RetrieveDocumentsTool(FakeVectorAccessGateway())},
    )

    with pytest.raises(DomainError) as exc_info:
        await executor.execute(
            tenant_context=tenant_context,
            proposal=ToolProposal(
                tool_name="retrieve_documents",
                tool_version="v1",
                arguments={"query_text": "credit policy"},
                reason="Need a tool.",
                risk_level="medium",
            ),
        )

    assert exc_info.value.code is ErrorCode.TOOL_AUTHORIZATION_FAILED
    assert exc_info.value.message == "Missing required scope for tool execution."


@pytest.mark.asyncio
async def test_tool_executor_rejects_invalid_argument_schema() -> None:
    executor = ToolExecutor(
        registry=ToolRegistry(
            definitions=(
                ToolDefinition(
                    tool_id="tool_retrieve_documents_v1",
                    name="retrieve_documents",
                    version="v1",
                    description="Retrieve authorized documents for the current tenant.",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query_text": {"type": "string"},
                            "top_k": {"type": "integer"},
                        },
                        "required": ["query_text"],
                    },
                    output_schema={"type": "object", "properties": {}},
                    risk_level="medium",
                    allowed_tenants=("tenant_credit",),
                    required_scopes=("rag:query",),
                ),
            )
        ),
        authorization_service=ToolAuthorizationService(),
        policy_engine=PolicyEngine(),
        handlers={"retrieve_documents": RetrieveDocumentsTool(FakeVectorAccessGateway())},
    )

    with pytest.raises(DomainError) as exc_info:
        await executor.execute(
            tenant_context=build_tenant_context(),
            proposal=ToolProposal(
                tool_name="retrieve_documents",
                tool_version="v1",
                arguments={"query_text": "credit policy", "top_k": "three"},
                reason="Need a tool.",
                risk_level="medium",
            ),
        )

    assert exc_info.value.code is ErrorCode.TOOL_SCHEMA_INVALID
    assert exc_info.value.message == "Invalid type for tool argument: top_k."


@pytest.mark.asyncio
async def test_tool_executor_times_out_slow_tool() -> None:
    executor = ToolExecutor(
        registry=ToolRegistry(
            definitions=(
                ToolDefinition(
                    tool_id="tool_slow_tool_v1",
                    name="slow_tool",
                    version="v1",
                    description="A slow read-only tool.",
                    input_schema={
                        "type": "object",
                        "properties": {},
                    },
                    output_schema={"type": "object", "properties": {}},
                    risk_level="low",
                    allowed_tenants=("tenant_credit",),
                    required_scopes=(),
                    timeout_ms=1,
                ),
            )
        ),
        authorization_service=ToolAuthorizationService(),
        policy_engine=PolicyEngine(),
        handlers={"slow_tool": SlowTool()},
    )

    with pytest.raises(DomainError) as exc_info:
        await executor.execute(
            tenant_context=build_tenant_context(),
            proposal=ToolProposal(
                tool_name="slow_tool",
                tool_version="v1",
                arguments={},
                reason="Need a tool.",
                risk_level="low",
            ),
        )

    assert exc_info.value.code is ErrorCode.TOOL_AUTHORIZATION_FAILED
    assert exc_info.value.message == "Tool execution timed out."
