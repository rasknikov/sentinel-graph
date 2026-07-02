from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from packages.common.db.dependencies import get_db_session
from packages.governance.audit.dependencies import get_audit_service
from packages.governance.audit.service import AuditService
from packages.governance.policy.dependencies import get_policy_engine
from packages.governance.policy.engine import PolicyEngine
from packages.rag.dependencies import get_vector_access_gateway
from packages.rag.vector_access_gateway import VectorAccessGateway
from packages.tools.authorization import ToolAuthorizationService
from packages.tools.builtin import RetrieveDocumentsTool
from packages.tools.executor import ToolExecutor
from packages.tools.registry import ToolRegistry
from packages.tools.schemas import ToolDefinition


def get_tool_registry() -> ToolRegistry:
    return ToolRegistry(
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
                        "document_id": {"type": "string"},
                        "version": {"type": "string"},
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
                allowed_tenants=("tenant_credit", "tenant_compliance"),
                required_scopes=("rag:query",),
                requires_hitl=False,
                timeout_ms=5000,
                idempotent=True,
                status="active",
                audit_level="full",
            ),
        )
    )


def get_tool_executor(
    registry: ToolRegistry = Depends(get_tool_registry),
    vector_access_gateway: VectorAccessGateway = Depends(get_vector_access_gateway),
    policy_engine: PolicyEngine = Depends(get_policy_engine),
    audit_service: AuditService = Depends(get_audit_service),
    db_session: AsyncSession = Depends(get_db_session),
) -> ToolExecutor:
    return ToolExecutor(
        registry=registry,
        authorization_service=ToolAuthorizationService(),
        policy_engine=policy_engine,
        handlers={
            "retrieve_documents": RetrieveDocumentsTool(
                vector_access_gateway=vector_access_gateway,
            ),
        },
        audit_service=audit_service,
        session=db_session,
    )
