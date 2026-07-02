import asyncio
from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from packages.common.errors import DomainError, ErrorCode
from packages.governance.audit.contracts import AuditEventWrite
from packages.governance.audit.service import AuditService
from packages.governance.policy.contracts import PolicyCheck, PolicyDecisionType
from packages.governance.policy.engine import PolicyEngine
from packages.security.tenant_context import TenantContext
from packages.tools.authorization import ToolAuthorizationService
from packages.tools.registry import ToolRegistry
from packages.tools.schemas import ToolDefinition, ToolProposal, ToolResult


ToolHandler = Callable[[TenantContext, dict], Awaitable[ToolResult]]


class ToolExecutor:
    def __init__(
        self,
        registry: ToolRegistry,
        authorization_service: ToolAuthorizationService,
        policy_engine: PolicyEngine,
        handlers: dict[str, ToolHandler],
        audit_service: AuditService | None = None,
        session: AsyncSession | None = None,
    ) -> None:
        self._registry = registry
        self._authorization_service = authorization_service
        self._policy_engine = policy_engine
        self._handlers = handlers
        self._audit_service = audit_service
        self._session = session

    async def execute(
        self,
        *,
        tenant_context: TenantContext,
        proposal: ToolProposal,
    ) -> ToolResult:
        try:
            tool_definition = self._registry.get_tool(
                name=proposal.tool_name,
                version=proposal.tool_version,
                trace_id=tenant_context.trace_id,
            )
            await self._record_event(
                tenant_context=tenant_context,
                event_type="tool_call_proposed",
                message=f"Tool proposal received for {tool_definition.name}:{tool_definition.version}.",
            )

            self._validate_arguments_schema(
                arguments=proposal.arguments,
                tool_definition=tool_definition,
                trace_id=tenant_context.trace_id,
            )
            self._authorization_service.authorize(
                tenant_context=tenant_context,
                tool_definition=tool_definition,
            )
            self._enforce_policy(
                tenant_context=tenant_context,
                tool_definition=tool_definition,
            )

            handler = self._get_handler(
                tool_definition=tool_definition,
                trace_id=tenant_context.trace_id,
            )

            result = await asyncio.wait_for(
                handler(tenant_context, proposal.arguments),
                timeout=tool_definition.timeout_ms / 1000,
            )
            await self._record_event(
                tenant_context=tenant_context,
                event_type="tool_executed",
                message=f"Tool executed successfully: {tool_definition.name}:{tool_definition.version}.",
            )
            return result
        except TimeoutError as exc:
            await self._record_event(
                tenant_context=tenant_context,
                event_type="tool_call_timed_out",
                message=f"Tool execution timed out for {proposal.tool_name}:{proposal.tool_version}.",
                error_code=ErrorCode.TOOL_AUTHORIZATION_FAILED,
            )
            raise DomainError(
                code=ErrorCode.TOOL_AUTHORIZATION_FAILED,
                message="Tool execution timed out.",
                trace_id=tenant_context.trace_id,
                cause=exc,
            ) from exc
        except DomainError as exc:
            await self._record_event(
                tenant_context=tenant_context,
                event_type="tool_call_denied",
                message=f"Tool execution denied for {proposal.tool_name}:{proposal.tool_version}.",
                error_code=exc.code,
            )
            raise

    def _enforce_policy(
        self,
        *,
        tenant_context: TenantContext,
        tool_definition: ToolDefinition,
    ) -> None:
        decision = self._policy_engine.evaluate(
            tenant_context,
            PolicyCheck(
                action="tool.execute",
                required_scopes=tool_definition.required_scopes,
                resource_id=tool_definition.tool_id,
            ),
        )

        if decision.decision is PolicyDecisionType.DENY:
            raise DomainError(
                code=decision.error_code or ErrorCode.POLICY_DENIED,
                message=decision.reason,
                trace_id=tenant_context.trace_id,
            )

        if tool_definition.requires_hitl:
            raise DomainError(
                code=ErrorCode.HITL_REQUIRED,
                message="Tool execution requires human approval.",
                trace_id=tenant_context.trace_id,
            )

    def _get_handler(
        self,
        *,
        tool_definition: ToolDefinition,
        trace_id: str,
    ) -> ToolHandler:
        handler = self._handlers.get(tool_definition.name)

        if handler is None:
            raise DomainError(
                code=ErrorCode.TOOL_NOT_FOUND,
                message="Tool handler is not registered.",
                trace_id=trace_id,
            )

        return handler

    def _validate_arguments_schema(
        self,
        *,
        arguments: dict,
        tool_definition: ToolDefinition,
        trace_id: str,
    ) -> None:
        input_schema = tool_definition.input_schema

        if input_schema.get("type") != "object":
            raise DomainError(
                code=ErrorCode.TOOL_SCHEMA_INVALID,
                message="Tool input schema must define an object payload.",
                trace_id=trace_id,
            )

        properties = input_schema.get("properties", {})
        required_fields = tuple(input_schema.get("required", ()))

        for field_name in required_fields:
            if field_name not in arguments:
                raise DomainError(
                    code=ErrorCode.TOOL_SCHEMA_INVALID,
                    message=f"Missing required tool argument: {field_name}.",
                    trace_id=trace_id,
                )

        for field_name, field_value in arguments.items():
            schema = properties.get(field_name)
            if schema is None:
                raise DomainError(
                    code=ErrorCode.TOOL_SCHEMA_INVALID,
                    message=f"Unknown tool argument: {field_name}.",
                    trace_id=trace_id,
                )

            expected_type = schema.get("type")
            if not self._matches_schema_type(field_value, expected_type):
                raise DomainError(
                    code=ErrorCode.TOOL_SCHEMA_INVALID,
                    message=f"Invalid type for tool argument: {field_name}.",
                    trace_id=trace_id,
                )

    def _matches_schema_type(
        self,
        value: object,
        expected_type: str | None,
    ) -> bool:
        if expected_type is None:
            return True

        type_checks = {
            "string": lambda candidate: isinstance(candidate, str),
            "integer": lambda candidate: isinstance(candidate, int) and not isinstance(candidate, bool),
            "number": lambda candidate: isinstance(candidate, (int, float)) and not isinstance(candidate, bool),
            "boolean": lambda candidate: isinstance(candidate, bool),
            "object": lambda candidate: isinstance(candidate, dict),
            "array": lambda candidate: isinstance(candidate, list),
        }

        checker = type_checks.get(expected_type)
        return True if checker is None else checker(value)

    async def _record_event(
        self,
        *,
        tenant_context: TenantContext,
        event_type: str,
        message: str,
        error_code: ErrorCode | None = None,
    ) -> None:
        if self._audit_service is None or self._session is None:
            return

        await self._audit_service.record_event(
            session=self._session,
            event=AuditEventWrite(
                tenant_id=tenant_context.tenant_id,
                user_id=tenant_context.user_id,
                request_id=tenant_context.request_id,
                trace_id=tenant_context.trace_id,
                event_type=event_type,
                message=message,
                error_code=error_code,
            ),
        )
