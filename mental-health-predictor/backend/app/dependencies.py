"""FastAPI dependencies shared by routes."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from fastapi import Request

from app.config import Settings
from app.errors import AppError
from app.rate_limit import SlidingWindowRateLimiter, resolve_client_ip
from app.services.model_service import ModelService


def get_model(request: Request) -> ModelService:
    model: ModelService = request.app.state.model
    return model


def rate_limit(scope: Literal["predict", "general"]) -> Callable[[Request], None]:
    """Dependency factory. Raises a 429 AppError when the caller is over the limit."""

    def dependency(request: Request) -> None:
        settings: Settings = request.app.state.settings
        limiter: SlidingWindowRateLimiter = request.app.state.limiter
        limit = settings.rate_limit_predict_per_minute if scope == "predict" else settings.rate_limit_general_per_minute
        peer = request.client.host if request.client else None
        ip = resolve_client_ip(request.headers.get("x-forwarded-for", ""), peer, settings.trust_proxy_headers)
        result = limiter.hit(f"{scope}:{ip}", limit, 60.0)
        if not result.allowed:
            raise AppError(
                status_code=429,
                code="rate_limited",
                message="Too many requests. Wait a moment and try again.",
                headers={"Retry-After": str(result.retry_after_seconds)},
            )

    return dependency
