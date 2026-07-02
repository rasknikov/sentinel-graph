from packages.common.errors import DomainError, ErrorCode
from packages.security.tenant_context import TenantContext
from packages.tools.schemas import ToolDefinition


class ToolAuthorizationService:
    def authorize(
        self,
        *,
        tenant_context: TenantContext,
        tool_definition: ToolDefinition,
    ) -> None:
        self._ensure_tool_is_active(
            tool_definition=tool_definition,
            trace_id=tenant_context.trace_id,
        )
        self._ensure_tenant_is_allowed(
            tenant_context=tenant_context,
            tool_definition=tool_definition,
        )
        self._ensure_required_scopes(
            tenant_context=tenant_context,
            tool_definition=tool_definition,
        )

    def _ensure_tool_is_active(
        self,
        *,
        tool_definition: ToolDefinition,
        trace_id: str,
    ) -> None:
        if tool_definition.status != "active":
            raise DomainError(
                code=ErrorCode.TOOL_AUTHORIZATION_FAILED,
                message="Requested tool is inactive.",
                trace_id=trace_id,
            )

    def _ensure_tenant_is_allowed(
        self,
        *,
        tenant_context: TenantContext,
        tool_definition: ToolDefinition,
    ) -> None:
        if tenant_context.tenant_id not in tool_definition.allowed_tenants:
            raise DomainError(
                code=ErrorCode.TOOL_AUTHORIZATION_FAILED,
                message="Tenant is not allowed to execute this tool.",
                trace_id=tenant_context.trace_id,
            )

    def _ensure_required_scopes(
        self,
        *,
        tenant_context: TenantContext,
        tool_definition: ToolDefinition,
    ) -> None:
        missing_scopes = tuple(
            scope
            for scope in tool_definition.required_scopes
            if scope not in tenant_context.scopes
        )

        if missing_scopes:
            raise DomainError(
                code=ErrorCode.TOOL_AUTHORIZATION_FAILED,
                message="Missing required scope for tool execution.",
                trace_id=tenant_context.trace_id,
            )