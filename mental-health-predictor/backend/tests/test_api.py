"""HTTP-level tests: status codes, error format, headers, rate limiting, logging policy.

These need FastAPI and httpx. They run in CI and on a normal developer machine.
"""

from __future__ import annotations

import logging

import pytest

pytest.importorskip("fastapi", reason="fastapi is not installed in this environment; runs in CI")
pytest.importorskip("httpx", reason="httpx is not installed in this environment; runs in CI")

from fastapi.testclient import TestClient  # noqa: E402

from app.config import load_settings  # noqa: E402
from app.main import create_app  # noqa: E402

HASH = "b" * 64


def build_client(model_service, **env) -> TestClient:
    settings = load_settings({"APP_ENV": "local", "MODEL_PATH": "unused.pkl", **env})
    return TestClient(create_app(settings=settings, model=model_service))


@pytest.fixture
def client(model_service):
    with build_client(model_service) as test_client:
        yield test_client


def assert_standard_error(response, status, code):
    assert response.status_code == status
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == code
    assert body["error"]["request_id"] == response.headers["x-request-id"]
    assert "Traceback" not in response.text


# --- health -----------------------------------------------------------------------------------


def test_liveness_is_ok_and_not_cacheable(client):
    response = client.get("/api/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "components": None}
    assert response.headers["cache-control"] == "no-store"


def test_readiness_runs_the_model(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["components"] == {"model": "ok"}


def test_readiness_returns_503_when_the_model_is_failing(model_service):
    class Broken:
        def predict(self, _frame):
            raise RuntimeError("model went bad")

    original = model_service._pipeline  # noqa: SLF001
    model_service._pipeline = Broken()  # noqa: SLF001
    try:
        with build_client(model_service) as test_client:
            response = test_client.get("/api/health")
    finally:
        model_service._pipeline = original  # noqa: SLF001
    assert response.status_code == 503
    assert response.json()["status"] == "degraded"


# --- options ----------------------------------------------------------------------------------


def test_options_come_from_the_model_and_include_limits(client):
    body = client.get("/api/options").json()
    assert "Other" in body["countries"]
    assert body["stress_levels"] == ["Low", "Medium", "High", "Very High"]
    assert body["limits"]["age"] == {"min": 13, "max": 100}
    assert body["training_ranges"]["age"] == {"min": 18, "max": 24}
    assert client.get("/api/options").headers["cache-control"] == "public, max-age=300"


# --- predict: happy path ----------------------------------------------------------------------


def test_valid_request_returns_an_estimate(client, valid_payload):
    response = client.post("/api/predict", json=valid_payload)
    assert response.status_code == 200
    body = response.json()
    assert 3.6 <= body["score"] <= 9.4
    assert body["band"] in {"below_typical", "typical", "above_typical"}
    assert body["scale"] == {"min": 3.6, "max": 9.4}
    assert body["typical_range"] == {"min": 5.1, "max": 7.1}
    assert "not a diagnosis" in body["disclaimer"]
    assert response.headers["cache-control"] == "no-store"


def test_age_outside_training_data_is_accepted_with_a_warning(client, valid_payload):
    body = client.post("/api/predict", json={**valid_payload, "age": 40}).json()
    assert any("Age (40)" in w for w in body["warnings"])


# --- predict: bad input -----------------------------------------------------------------------


def test_garbage_json_gets_a_clean_400_in_the_standard_format(client):
    response = client.post("/api/predict", content=b"{not json", headers={"content-type": "application/json"})
    assert_standard_error(response, 400, "invalid_request")


def test_missing_fields_are_named(client):
    response = client.post("/api/predict", json={"age": 21})
    assert_standard_error(response, 400, "invalid_request")
    fields = {d["field"] for d in response.json()["error"]["details"]}
    assert {"gender", "stress_level", "sleep_hours_per_night"} <= fields


def test_unknown_extra_field_is_rejected(client, valid_payload):
    assert_standard_error(client.post("/api/predict", json={**valid_payload, "is_admin": True}), 400, "invalid_request")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("age", 5),
        ("age", 101),
        ("sleep_hours_per_night", -1),
        ("sleep_hours_per_night", 25),
        ("daily_unlocks", 5000),
        ("age", "twenty"),
        ("stress_level", "Extreme"),
    ],
)
def test_out_of_range_or_wrong_type_values_are_rejected(client, valid_payload, field, value):
    response = client.post("/api/predict", json={**valid_payload, field: value})
    assert_standard_error(response, 400, "invalid_request")
    assert response.json()["error"]["details"][0]["field"] == field


def test_nan_is_rejected(client, valid_payload):
    raw = (
        '{"age":21,"gender":"Female","country":"India","academic_level":"Graduate",'
        '"most_used_platform":"TikTok","purpose_of_use":"Education","avg_daily_usage_hours":4,'
        '"daily_unlocks":100,"study_hours":2,"physical_activity_hours":1,"sleep_hours_per_night":NaN,'
        '"stress_level":"Low"}'
    )
    response = client.post("/api/predict", content=raw, headers={"content-type": "application/json"})
    assert_standard_error(response, 400, "invalid_request")


def test_unknown_category_is_rejected_and_the_value_is_not_echoed(client, valid_payload):
    response = client.post("/api/predict", json={**valid_payload, "gender": "<script>alert(1)</script>"})
    assert_standard_error(response, 400, "invalid_request")
    assert "<script>" not in response.text
    assert response.json()["error"]["details"][0]["field"] == "gender"


def test_oversized_body_is_refused(client):
    response = client.post("/api/predict", content=b"x" * 20_000, headers={"content-type": "application/json"})
    assert_standard_error(response, 413, "payload_too_large")


# --- other errors -----------------------------------------------------------------------------


def test_unknown_route_uses_the_standard_format(client):
    assert_standard_error(client.get("/api/nope"), 404, "not_found")


def test_wrong_method_uses_the_standard_format(client):
    assert_standard_error(client.get("/api/predict"), 405, "method_not_allowed")


def test_unexpected_failure_returns_a_generic_500_and_logs_the_detail(model_service, valid_payload, caplog):
    class Exploding:
        def predict(self, _frame):
            raise RuntimeError("secret internal detail")

    original = model_service._pipeline  # noqa: SLF001
    model_service._pipeline = Exploding()  # noqa: SLF001
    try:
        with caplog.at_level(logging.ERROR), build_client(model_service) as test_client:
            response = test_client.post("/api/predict", json=valid_payload)
    finally:
        model_service._pipeline = original  # noqa: SLF001
    assert_standard_error(response, 500, "internal_error")
    assert "secret internal detail" not in response.text
    assert "secret internal detail" in caplog.text


# --- request IDs and headers ------------------------------------------------------------------


def test_a_well_formed_request_id_is_echoed(client):
    response = client.get("/api/health/live", headers={"X-Request-ID": "abc-12345678"})
    assert response.headers["x-request-id"] == "abc-12345678"


@pytest.mark.parametrize("bad", ["short", "has spaces in it!!", "x" * 200, "<script>alert(1)</script>"])
def test_a_malformed_request_id_is_replaced(client, bad):
    response = client.get("/api/health/live", headers={"X-Request-ID": bad})
    assert response.headers["x-request-id"] != bad
    assert len(response.headers["x-request-id"]) == 32


def test_security_headers_are_present_and_hsts_only_outside_local(client, model_service):
    headers = client.get("/api/health/live").headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "no-referrer"
    assert "default-src 'none'" in headers["content-security-policy"]
    assert "strict-transport-security" not in headers

    with build_client(model_service, APP_ENV="staging") as staging:
        assert "strict-transport-security" in staging.get("/api/health/live").headers


def test_docs_exist_locally_and_are_gone_in_production(client, model_service):
    assert client.get("/docs").status_code == 200
    with build_client(model_service, APP_ENV="production", MODEL_SHA256=HASH) as production:
        assert production.get("/docs").status_code == 404
        assert production.get("/openapi.json").status_code == 404


# --- rate limiting ----------------------------------------------------------------------------


def test_predict_is_rate_limited_with_retry_after(model_service, valid_payload):
    with build_client(model_service, RATE_LIMIT_PREDICT_PER_MINUTE="2") as limited:
        assert limited.post("/api/predict", json=valid_payload).status_code == 200
        assert limited.post("/api/predict", json=valid_payload).status_code == 200
        blocked = limited.post("/api/predict", json=valid_payload)
    assert_standard_error(blocked, 429, "rate_limited")
    assert int(blocked.headers["retry-after"]) >= 1


def test_health_checks_are_never_rate_limited(model_service):
    with build_client(model_service, RATE_LIMIT_GENERAL_PER_MINUTE="1", RATE_LIMIT_PREDICT_PER_MINUTE="1") as limited:
        assert all(limited.get("/api/health").status_code == 200 for _ in range(5))
        assert all(limited.get("/api/health/live").status_code == 200 for _ in range(5))


def test_options_use_the_general_limit(model_service):
    with build_client(model_service, RATE_LIMIT_GENERAL_PER_MINUTE="1") as limited:
        assert limited.get("/api/options").status_code == 200
        assert limited.get("/api/options").status_code == 429


# --- CORS -------------------------------------------------------------------------------------


def test_cors_allows_only_the_configured_origin(model_service):
    with build_client(model_service, CORS_ORIGINS="https://app.example.com") as cors_client:
        allowed = cors_client.options(
            "/api/predict",
            headers={
                "Origin": "https://app.example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        denied = cors_client.options(
            "/api/predict",
            headers={"Origin": "https://evil.example.com", "Access-Control-Request-Method": "POST"},
        )
    assert allowed.headers["access-control-allow-origin"] == "https://app.example.com"
    assert "access-control-allow-origin" not in denied.headers


# --- logging policy ---------------------------------------------------------------------------


def test_request_logs_contain_no_inputs_and_no_client_ip(client, valid_payload, caplog):
    distinctive = {**valid_payload, "country": "Zzyzx-Land", "age": 23}
    with caplog.at_level(logging.INFO):
        client.post("/api/predict", json=distinctive)
    request_logs = [r for r in caplog.records if getattr(r, "event", None) == "request"]
    assert request_logs, "expected one structured request log line"
    assert request_logs[0].status == 200
    assert "Zzyzx-Land" not in caplog.text
    assert "testclient" not in caplog.text
