from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.error_handlers import register_exception_handlers
from app.api.health import router as health_router
from app.api.v1.router import router as api_v1_router
from app.core.config import Settings, get_settings
from app.core.database import Database
from app.core.logging import configure_logging
from app.core.rate_limit import FixedWindowRateLimiter
from app.core.request_id import RequestContextMiddleware


class VercelServicePathMiddleware(BaseHTTPMiddleware):
    """Expose the backend service below the public /backend route prefix."""

    async def dispatch(self, request, call_next):  # type: ignore[no-untyped-def]
        path = request.scope["path"]
        if path == "/backend" or path.startswith("/backend/"):
            request.scope["root_path"] = f"{request.scope.get('root_path', '')}/backend"
            request.scope["path"] = path.removeprefix("/backend") or "/"
        return await call_next(request)


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    logger = configure_logging()
    database = Database(app_settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        logger.info("Application started")
        try:
            yield
        finally:
            await database.dispose()
            logger.info("Application stopped")

    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        description="API سامانهٔ مدیریت پروژه برای تیم‌های فارسی‌زبان.",
        openapi_url="/api/v1/openapi.json" if app_settings.expose_docs else None,
        docs_url="/docs" if app_settings.expose_docs else None,
        redoc_url="/redoc" if app_settings.expose_docs else None,
        lifespan=lifespan,
    )
    app.state.logger = logger
    app.state.database = database
    app.state.settings = app_settings
    app.state.rate_limiter = FixedWindowRateLimiter()
    app.add_middleware(VercelServicePathMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(api_v1_router)
    return app


app = create_app()
