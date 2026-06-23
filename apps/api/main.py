from fastapi import FastAPI

from apps.api.core.error_handlers import register_error_handlers
from apps.api.routes.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="SentinelGraph API")
    register_error_handlers(app)
    app.include_router(health_router)
    return app


app = create_app()
