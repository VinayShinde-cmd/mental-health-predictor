"""Application factory.

Run with:  uvicorn app.main:create_app --factory --no-access-log
Configuration comes from environment variables (see backend/.env.example) and is validated here,
so a bad setup stops the process with a clear message instead of failing on the first request.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, load_settings
from app.errors import register_exception_handlers
from app.logging_config import configure_logging
from app.middleware import RequestContextMiddleware
from app.rate_limit import SlidingWindowRateLimiter
from app.routes import health, predict
from app.services.model_service import ModelService

logger = logging.getLogger("app")


def create_app(settings: Settings | None = None, model: ModelService | None = None) -> FastAPI:
    """``settings`` and ``model`` can be injected (tests); otherwise they come from the environment."""
    settings = settings or load_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if getattr(app.state, "model", None) is None:
            app.state.model = ModelService.load(settings.model_path, settings.model_sha256)
        logger.info(
            "startup_complete",
            extra={"event": "startup_complete", "app_env": settings.app_env, "model_id": app.state.model.model_id},
        )
        yield
        logger.info("shutdown", extra={"event": "shutdown"})

    # Interactive docs describe every endpoint to anyone; keep them out of production.
    docs = {} if not settings.is_production else {"docs_url": None, "redoc_url": None, "openapi_url": None}
    app = FastAPI(title="Mental health score estimator API", version="0.1.0", lifespan=lifespan, **docs)

    app.state.settings = settings
    app.state.model = model
    app.state.limiter = SlidingWindowRateLimiter()

    register_exception_handlers(app)
    # Added first so it sits inside CORS: its error responses (413, 500) still get CORS headers.
    app.add_middleware(RequestContextMiddleware, settings=settings)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type", "X-Request-ID"],
            expose_headers=["X-Request-ID", "Retry-After"],
            max_age=600,
        )

    app.include_router(health.router)
    app.include_router(predict.router)
    return app
