import pytest

from app.config import ConfigError, load_settings

BASE = {"APP_ENV": "local", "MODEL_PATH": "models/m.pkl"}
HASH = "a" * 64


def test_minimal_local_config_gets_safe_defaults():
    settings = load_settings(BASE)
    assert settings.app_env == "local"
    assert settings.model_sha256 is None
    assert settings.cors_origins == ()
    assert settings.rate_limit_predict_per_minute == 30
    assert settings.trust_proxy_headers is False


def test_missing_required_values_are_all_reported_at_once():
    with pytest.raises(ConfigError) as caught:
        load_settings({})
    message = str(caught.value)
    assert "APP_ENV" in message
    assert "MODEL_PATH" in message


def test_unknown_app_env_is_rejected():
    with pytest.raises(ConfigError, match="APP_ENV"):
        load_settings({**BASE, "APP_ENV": "prod"})


def test_production_requires_model_hash():
    with pytest.raises(ConfigError, match="MODEL_SHA256 is required"):
        load_settings({**BASE, "APP_ENV": "production"})


def test_production_with_hash_is_accepted_and_lowercased():
    settings = load_settings({**BASE, "APP_ENV": "production", "MODEL_SHA256": HASH.upper()})
    assert settings.is_production
    assert settings.model_sha256 == HASH


def test_malformed_hash_is_rejected():
    with pytest.raises(ConfigError, match="64 hexadecimal"):
        load_settings({**BASE, "MODEL_SHA256": "abc"})


def test_debug_logging_is_rejected_in_production():
    with pytest.raises(ConfigError, match="DEBUG"):
        load_settings({**BASE, "APP_ENV": "production", "MODEL_SHA256": HASH, "LOG_LEVEL": "debug"})


def test_wildcard_cors_is_rejected_in_production_but_allowed_locally():
    with pytest.raises(ConfigError, match="CORS_ORIGINS"):
        load_settings({**BASE, "APP_ENV": "production", "MODEL_SHA256": HASH, "CORS_ORIGINS": "*"})
    assert load_settings({**BASE, "CORS_ORIGINS": "*"}).cors_origins == ("*",)


def test_cors_origin_with_a_path_is_rejected():
    with pytest.raises(ConfigError, match="CORS_ORIGINS"):
        load_settings({**BASE, "CORS_ORIGINS": "https://example.com/app"})


def test_cors_origins_are_split_and_trailing_slash_trimmed():
    settings = load_settings({**BASE, "CORS_ORIGINS": "https://a.example.com/, http://localhost:5173"})
    assert settings.cors_origins == ("https://a.example.com", "http://localhost:5173")


@pytest.mark.parametrize("value", ["0", "-5", "10001", "lots"])
def test_bad_rate_limits_are_rejected(value):
    with pytest.raises(ConfigError, match="RATE_LIMIT_PREDICT_PER_MINUTE"):
        load_settings({**BASE, "RATE_LIMIT_PREDICT_PER_MINUTE": value})


@pytest.mark.parametrize(("raw", "expected"), [("true", True), ("1", True), ("false", False), ("off", False)])
def test_boolean_parsing(raw, expected):
    assert load_settings({**BASE, "TRUST_PROXY_HEADERS": raw}).trust_proxy_headers is expected


def test_unparseable_boolean_is_rejected():
    with pytest.raises(ConfigError, match="TRUST_PROXY_HEADERS"):
        load_settings({**BASE, "TRUST_PROXY_HEADERS": "maybe"})
