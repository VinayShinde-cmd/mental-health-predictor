"""Request context: request ID, size cap, access log, security headers, unexpected-error handling."""

from __future__ import annotations

import logging
import re
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.config import Settings
from app.errors import error_response
from app.logging_config import request_id_var

logger = logging.getLogger("app.request")

MAX_BODY_BYTES = 10_000  # the largest valid payload is well under 1 KB
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
_DOC_PATHS = ("/docs", "/redoc", "/openapi.json")  # only exist outside production


def apply_security_headers(response: Response, path: str, settings: Settings) -> None:
    headers = response.headers
    headers["X-Content-Type-Options"] = "nosniff"
    headers["Referrer-Policy"] = "no-referrer"
    headers["X-Frame-Options"] = "DENY"
    if not path.startswith(_DOC_PATHS):
        # The API only returns JSON, so nothing may load or frame from it.
        headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    if not settings.is_local:
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._settings = settings

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get("x-request-id", "")
        request_id = incoming if _REQUEST_ID_RE.fullmatch(incoming) else uuid.uuid4().hex
        request.state.request_id = request_id
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        try:
            declared = request.headers.get("content-length", "")
            if declared.isdigit() and int(declared) > MAX_BODY_BYTES:
                response: Response = error_response(413, "payload_too_large", "Request body is too large.", request_id)
            else:
                try:
                    response = await call_next(request)
                except Exception:
                    # Full detail goes to the log only; the caller gets a generic message.
                    logger.exception("unhandled_error", extra={"event": "unhandled_error"})
                    response = error_response(
                        500, "internal_error", "Something went wrong on our side. Try again shortly.", request_id
                    )
            response.headers["X-Request-ID"] = request_id
            apply_security_headers(response, request.url.path, self._settings)
            logger.info(
                "request",
                extra={
                    "event": "request",
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                },
            )
            return response
        finally:
            request_id_var.reset(token)
