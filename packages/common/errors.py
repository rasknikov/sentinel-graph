from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ErrorCode(StrEnum):
    AUTH_INVALID = "AUTH_INVALID"
    TENANT_CONTEXT_MISSING = "TENANT_CONTEXT_MISSING"
    TENANT_ACCESS_DENIED = "TENANT_ACCESS_DENIED"
    TENANT_MISMATCH = "TENANT_MISMATCH"
    TENANT_INACTIVE = "TENANT_INACTIVE"
    CROSS_TENANT_ACCESS_DENIED = "CROSS_TENANT_ACCESS_DENIED"
    TENANT_BUDGET_EXCEEDED = "TENANT_BUDGET_EXCEEDED"
    TENANT_MODEL_NOT_ALLOWED = "TENANT_MODEL_NOT_ALLOWED"
    TENANT_TOOL_NOT_ALLOWED = "TENANT_TOOL_NOT_ALLOWED"
    TENANT_DOCUMENT_ACCESS_DENIED = "TENANT_DOCUMENT_ACCESS_DENIED"
    DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
    DOCUMENT_VERSION_NOT_FOUND = "DOCUMENT_VERSION_NOT_FOUND"
    POLICY_DENIED = "POLICY_DENIED"
    MODEL_NOT_ALLOWED = "MODEL_NOT_ALLOWED"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    NO_SAFE_FALLBACK = "NO_SAFE_FALLBACK"
    TOKEN_BUDGET_EXCEEDED = "TOKEN_BUDGET_EXCEEDED"
    COST_BUDGET_EXCEEDED = "COST_BUDGET_EXCEEDED"
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    TOOL_SCHEMA_INVALID = "TOOL_SCHEMA_INVALID"
    TOOL_AUTHORIZATION_FAILED = "TOOL_AUTHORIZATION_FAILED"
    RETRIEVAL_ACCESS_DENIED = "RETRIEVAL_ACCESS_DENIED"
    GROUNDING_FAILED = "GROUNDING_FAILED"
    PII_POLICY_VIOLATION = "PII_POLICY_VIOLATION"
    PROMPT_INJECTION_DETECTED = "PROMPT_INJECTION_DETECTED"
    HITL_REQUIRED = "HITL_REQUIRED"
    OUTPUT_VALIDATION_FAILED = "OUTPUT_VALIDATION_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class APIError(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: ErrorCode
    message: str = Field(
        ...,
        min_length=1,
        description="Safe message intended for API clients.",
    )
    trace_id: str = Field(
        ...,
        min_length=1,
        description="Trace identifier that allows later investigation.",
    )

    @model_validator(mode="after")
    def validate_safe_message(self) -> "APIError":
        # Safe API errors must stay single-line and trimmed to avoid
        # accidental leakage of stack traces or multiline internals.
        if self.message != self.message.strip():
            raise ValueError("API error message must not contain surrounding whitespace.")

        if "\n" in self.message or "\r" in self.message:
            raise ValueError("API error message must be single-line.")

        return self


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True)

    error: APIError


class DomainError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        trace_id: str,
        *,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.trace_id = trace_id
        self.details = details or {}
        self.cause = cause
        super().__init__(message)

    def to_api_error(self) -> APIError:
        return APIError(
            code=self.code,
            message=self.message,
            trace_id=self.trace_id,
        )

    def to_envelope(self) -> ErrorEnvelope:
        return ErrorEnvelope(error=self.to_api_error())
