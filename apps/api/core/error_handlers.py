from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from packages.common.errors import DomainError, ErrorCode


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        status_code = _status_code_for_error(exc.code)
        return JSONResponse(
            status_code=status_code,
            content=exc.to_envelope().model_dump(mode="json"),
        )


def _status_code_for_error(code: ErrorCode) -> int:
    if code in {
        ErrorCode.DOCUMENT_NOT_FOUND,
        ErrorCode.DOCUMENT_VERSION_NOT_FOUND,
    }:
        return status.HTTP_404_NOT_FOUND

    if code in {
        ErrorCode.AUTH_INVALID,
        ErrorCode.TENANT_ACCESS_DENIED,
        ErrorCode.TENANT_ACCESS_DENIED,
        ErrorCode.CROSS_TENANT_ACCESS_DENIED,
        ErrorCode.TOOL_AUTHORIZATION_FAILED,
        ErrorCode.RETRIEVAL_ACCESS_DENIED,
        ErrorCode.POLICY_DENIED,
    }:
        return status.HTTP_403_FORBIDDEN

    if code in {
        ErrorCode.TENANT_CONTEXT_MISSING,
        ErrorCode.TENANT_MISMATCH,
        ErrorCode.TENANT_INACTIVE,
        ErrorCode.OUTPUT_VALIDATION_FAILED,
        ErrorCode.GROUNDING_FAILED,
    }:
        return status.HTTP_400_BAD_REQUEST

    return status.HTTP_500_INTERNAL_SERVER_ERROR
