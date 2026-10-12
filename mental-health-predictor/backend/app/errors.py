"""One error format for the whole API (docs/decisions/0006)."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: list[dict[str, str]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        self.headers = headers or {}


def error_body(code: str, message: str, request_id: str, details: list[dict[str, str]] | None = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message, "request_id": request_id}
    if details:
        error["details"] = details
    return {"error": error}


def error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: str,
    details: list[dict[str, str]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    response_headers = {"X-Request-ID": request_id, **(headers or {})}
    return JSONResponse(
        status_code=status_code,
        content=error_body(code, message, request_id, details),
        headers=response_headers,
    )


def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", "-"))


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message, _request_id(request), exc.details, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Only the field path and rule text are returned. The submitted value is never echoed.
        details = [
            {
                "field": ".".join(str(part) for part in err["loc"] if part != "body") or "body",
                "message": str(err["msg"]),
            }
            for err in exc.errors()
        ]
        return error_response(400, "invalid_request", "Some fields are invalid.", _request_id(request), details)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        codes = {404: "not_found", 405: "method_not_allowed"}
        try:
            phrase = HTTPStatus(exc.status_code).phrase
        except ValueError:
            phrase = "Request failed"
        return error_response(
            exc.status_code,
            codes.get(exc.status_code, "http_error"),
            phrase,
            _request_id(request),
            headers=dict(exc.headers or {}),
        )
