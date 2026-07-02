from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ToolDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    tool_id: str
    name: str
    version: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    risk_level: Literal["low", "medium", "high"]
    allowed_tenants: tuple[str, ...]
    required_scopes: tuple[str, ...]
    requires_hitl: bool = False
    timeout_ms: int = 5000
    idempotent: bool = True
    status: Literal["active", "inactive"] = "active"
    audit_level: Literal["minimal", "full"] = "full"


class ToolProposal(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["tool_call"] = "tool_call"
    tool_name: str
    tool_version: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    reason: str
    risk_level: Literal["low", "medium", "high"]


class ToolResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    tool_name: str
    tool_version: str
    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolError(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    message: str
    retryable: bool = False