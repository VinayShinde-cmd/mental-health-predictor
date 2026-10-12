"""Structured JSON logging with request IDs and redaction of sensitive field names.

Policy (docs/decisions/0005): request bodies, query strings, headers and client IPs are never logged.
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

SENSITIVE_FRAGMENTS = ("password", "token", "secret", "authorization", "cookie", "api_key", "apikey")
REDACTED = "[REDACTED]"
_HANDLER_NAME = "app-json-stdout"

# Attributes every LogRecord has; anything else on a record came from `extra=`.
_RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime", "taskName"}


def redact(value: Any) -> Any:
    """Return a copy of ``value`` with the values of sensitive-looking keys masked (recursive)."""
    if isinstance(value, dict):
        return {
            key: REDACTED if any(f in str(key).lower() for f in SENSITIVE_FRAGMENTS) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list | tuple):
        return [redact(item) for item in value]
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        extras = {k: v for k, v in record.__dict__.items() if k not in _RESERVED and not k.startswith("_")}
        payload.update(redact(extras))
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str) -> None:
    """Send all logs to stdout as JSON. Safe to call more than once."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.set_name(_HANDLER_NAME)
    root = logging.getLogger()
    for existing in list(root.handlers):  # replace only our own handler from an earlier call
        if existing.get_name() == _HANDLER_NAME:
            root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(level)
    # Uvicorn's access log prints client IPs; the app writes its own request line instead.
    logging.getLogger("uvicorn.access").disabled = True
