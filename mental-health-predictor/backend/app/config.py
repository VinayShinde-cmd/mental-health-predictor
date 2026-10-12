"""Configuration read from environment variables and validated at startup.

The app refuses to start if anything is missing or malformed, and says what to fix.
Nothing in here has a hard-coded URL, key or ID. See ``backend/.env.example``.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

APP_ENVS = ("local", "staging", "production")
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off", ""}


class ConfigError(RuntimeError):
    """Raised when the environment is missing or has malformed settings."""


@dataclass(frozen=True)
class Settings:
    app_env: str
    model_path: Path
    model_sha256: str | None
    cors_origins: tuple[str, ...]
    log_level: str
    rate_limit_predict_per_minute: int
    rate_limit_general_per_minute: int
    trust_proxy_headers: bool

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_local(self) -> bool:
        return self.app_env == "local"


def _parse_int(env: Mapping[str, str], name: str, default: int, low: int, high: int, problems: list[str]) -> int:
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        problems.append(f"{name} must be a whole number between {low} and {high} (got a non-number).")
        return default
    if not low <= value <= high:
        problems.append(f"{name} must be between {low} and {high} (got {value}).")
    return value


def _parse_bool(env: Mapping[str, str], name: str, default: bool, problems: list[str]) -> bool:
    raw = env.get(name)
    if raw is None:
        return default
    lowered = raw.strip().lower()
    if lowered in _TRUE:
        return True
    if lowered in _FALSE:
        return False
    problems.append(f"{name} must be true or false (got {raw!r}).")
    return default


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Build Settings from ``env`` (defaults to ``os.environ``) or raise ConfigError listing every problem."""
    source: Mapping[str, str] = os.environ if env is None else env
    problems: list[str] = []

    app_env = source.get("APP_ENV", "").strip().lower()
    if app_env not in APP_ENVS:
        problems.append(f"APP_ENV is required and must be one of {', '.join(APP_ENVS)}.")
        app_env = "production"  # fail closed while we keep collecting problems
    is_production = app_env == "production"

    raw_model_path = source.get("MODEL_PATH", "").strip()
    if not raw_model_path:
        problems.append("MODEL_PATH is required: path to the trained model file (.pkl).")

    raw_sha = source.get("MODEL_SHA256", "").strip()
    model_sha256: str | None = None
    if raw_sha:
        if _SHA256_RE.match(raw_sha):
            model_sha256 = raw_sha.lower()
        else:
            problems.append("MODEL_SHA256 must be 64 hexadecimal characters.")
    elif is_production:
        problems.append("MODEL_SHA256 is required in production so the model file is verified before it is loaded.")

    origins = tuple(o.strip().rstrip("/") for o in source.get("CORS_ORIGINS", "").split(",") if o.strip())
    for origin in origins:
        if origin == "*" and is_production:
            problems.append("CORS_ORIGINS must list exact origins in production; '*' is not allowed.")
        elif origin != "*" and not re.match(r"^https?://[^/\s]+$", origin):
            problems.append(f"CORS_ORIGINS entry {origin!r} must look like https://example.com (no path).")

    log_level = source.get("LOG_LEVEL", "INFO").strip().upper() or "INFO"
    if log_level not in LOG_LEVELS:
        problems.append(f"LOG_LEVEL must be one of {', '.join(LOG_LEVELS)}.")
    elif log_level == "DEBUG" and is_production:
        problems.append("LOG_LEVEL=DEBUG is not allowed in production.")

    predict_limit = _parse_int(source, "RATE_LIMIT_PREDICT_PER_MINUTE", 30, 1, 10_000, problems)
    general_limit = _parse_int(source, "RATE_LIMIT_GENERAL_PER_MINUTE", 120, 1, 100_000, problems)
    trust_proxy = _parse_bool(source, "TRUST_PROXY_HEADERS", False, problems)

    if problems:
        bullet_list = "\n".join(f" - {p}" for p in problems)
        raise ConfigError(f"Invalid configuration. Fix these and restart:\n{bullet_list}")

    return Settings(
        app_env=app_env,
        model_path=Path(raw_model_path),
        model_sha256=model_sha256,
        cors_origins=origins,
        log_level=log_level,
        rate_limit_predict_per_minute=predict_limit,
        rate_limit_general_per_minute=general_limit,
        trust_proxy_headers=trust_proxy,
    )
