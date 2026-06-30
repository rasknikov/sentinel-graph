from fastapi import FastAPI

from apps.api.core.error_handlers import register_error_handlers
from apps.api.routes.context import router as context_router
from apps.api.routes.health import router as health_router
from packages.security.middleware import TenantContextMiddleware


def create_app() -> FastAPI:
    app = FastAPI(title="SentinelGraph API")
    app.add_middleware(TenantContextMiddleware)
    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(context_router)
    return app


app = create_app()
