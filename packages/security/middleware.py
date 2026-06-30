from collections.abc import Awaitable, Callable

from fastapi import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from packages.security.auth import build_tenant_context
from packages.security.jwt import JwtTokenValidator, TokenValidator
from packages.security.request_context import generate_request_id, generate_trace_id


PUBLIC_PATHS = {"/health"}


class TenantContextMiddleware:
    def __init__(
            self,
            app: ASGIApp,
            token_validator: TokenValidator | None = None,
    ) -> None:
        self.app = app
        self.token_validator = token_validator or JwtTokenValidator()

    async def __call__(
            self,
            scope: dict,
            receive: Callable[[], Awaitable[dict]],
            send: Callable[[dict], Awaitable[None]],
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive=receive)

        request_id = generate_request_id()
        trace_id = generate_trace_id()

        request.state.request_id = request_id
        request.state.trace_id = trace_id

        if request.url.path in PUBLIC_PATHS:
            await self.app(scope, receive, send)
            return

        authorization = request.headers.get("authorization")

        if not authorization or not authorization.startswith("Bearer "):
            response = JSONResponse(
                status_code=401,
                content={
                    "code": "authentication_required",
                    "message": "Authentication is required.",
                    "trace_id": trace_id,
                },
            )
            await response(scope, receive, send)
            return
        
        token = authorization.removeprefix("Bearer ").strip()

        try:
            claims = self.token_validator.validate(token)
            tenant_context = build_tenant_context(
                claims=claims,
                request_id=request_id,
                trace_id=trace_id,
            )
        except ValueError:
            response = JSONResponse(
                status_code=401,
                content={
                    "code": "invalid_authentication",
                    "message": "Authentication is invalid.",
                    "trace_id": trace_id,
                },
            )
            await response(scope, receive, send)
            return
        
        request.state.tenant_context = tenant_context

        await self.app(scope, receive, send)
