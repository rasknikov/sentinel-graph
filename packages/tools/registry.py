from packages.common.errors import DomainError, ErrorCode
from packages.tools.schemas import ToolDefinition


class ToolRegistry:
    def __init__(
        self,
        definitions: tuple[ToolDefinition, ...],
    ) -> None:
        self._definitions_by_key = {
            self._build_key(
                name=definition.name,
                version=definition.version,
            ): definition
            for definition in definitions
        }

    def get_tool(
        self,
        *,
        name: str,
        version: str,
        trace_id: str,
    ) -> ToolDefinition:
        key = self._build_key(name=name, version=version)
        definition = self._definitions_by_key.get(key)

        if definition is None:
            raise DomainError(
                code=ErrorCode.TOOL_NOT_FOUND,
                message="Requested tool is not registered.",
                trace_id=trace_id,
            )

        return definition

    def list_active_tools(self) -> tuple[ToolDefinition, ...]:
        return tuple(
            definition
            for definition in self._definitions_by_key.values()
            if definition.status == "active"
        )

    def _build_key(
        self,
        *,
        name: str,
        version: str,
    ) -> str:
        return f"{name}:{version}"