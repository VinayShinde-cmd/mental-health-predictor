import json
import logging

from app.logging_config import REDACTED, JsonFormatter, redact, request_id_var


def _record(message="hello", **extra):
    record = logging.LogRecord("test", logging.INFO, __file__, 1, message, (), None)
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_redact_masks_sensitive_keys_at_any_depth():
    cleaned = redact({"user": "ok", "Password": "x", "nested": {"api_key": "k", "list": [{"token": "t", "n": 1}]}})
    assert cleaned["user"] == "ok"
    assert cleaned["Password"] == REDACTED
    assert cleaned["nested"]["api_key"] == REDACTED
    assert cleaned["nested"]["list"][0] == {"token": REDACTED, "n": 1}


def test_redact_does_not_mutate_its_input():
    original = {"secret": "s"}
    redact(original)
    assert original == {"secret": "s"}


def test_log_line_is_json_with_request_id_and_extra_fields():
    token = request_id_var.set("req-12345678")
    try:
        line = JsonFormatter().format(_record("request", event="request", status=200))
    finally:
        request_id_var.reset(token)
    data = json.loads(line)
    assert data["message"] == "request"
    assert data["request_id"] == "req-12345678"
    assert data["status"] == 200
    assert data["level"] == "info"


def test_sensitive_extras_are_redacted_in_the_final_line():
    line = JsonFormatter().format(_record(authorization="Bearer abc", event="x"))
    assert "Bearer abc" not in line
    assert json.loads(line)["authorization"] == REDACTED


def test_exception_info_is_included_as_text():
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = logging.LogRecord("t", logging.ERROR, __file__, 1, "failed", (), sys.exc_info())
    assert "ValueError: boom" in json.loads(JsonFormatter().format(record))["exception"]
