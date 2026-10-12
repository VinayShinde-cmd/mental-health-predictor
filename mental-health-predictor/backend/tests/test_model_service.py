import warnings
from pathlib import Path

import pytest
from sklearn.exceptions import InconsistentVersionWarning
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline

from app.domain.exceptions import InvalidInputError
from app.services.model_service import ModelLoadError, ModelService, _sha256_of
from app.services.prediction_service import make_prediction

# --- loading ----------------------------------------------------------------------------------


def test_loads_and_reports_a_short_model_id(model_service, model_path):
    assert model_service.model_id == _sha256_of(model_path)[:12]


def test_accepts_the_correct_hash(model_path):
    assert ModelService.load(model_path, _sha256_of(model_path).upper()).model_id


def test_refuses_a_file_whose_hash_differs(model_path):
    with pytest.raises(ModelLoadError, match="does not match MODEL_SHA256"):
        ModelService.load(model_path, "0" * 64)


def test_missing_file_has_an_actionable_message(tmp_path):
    with pytest.raises(ModelLoadError, match="MODEL_PATH"):
        ModelService.load(tmp_path / "nope.pkl", None)


def test_corrupted_file_is_reported_without_leaking_internals(tmp_path):
    bad = tmp_path / "bad.pkl"
    bad.write_bytes(b"this is not a pickle")
    with pytest.raises(ModelLoadError, match="could not be loaded"):
        ModelService.load(bad, None)


def test_sklearn_version_mismatch_is_an_error_not_a_warning(model_path, monkeypatch):
    def fake_load(_path: Path):
        warnings.warn(
            InconsistentVersionWarning(
                estimator_name="Pipeline", current_sklearn_version="9.9.9", original_sklearn_version="1.0.0"
            ),
            stacklevel=2,
        )

    monkeypatch.setattr("app.services.model_service.joblib.load", fake_load)
    with pytest.raises(ModelLoadError, match=r"1\.0\.0.*9\.9\.9"):
        ModelService.load(model_path, None)


def test_a_model_with_different_columns_is_rejected():
    import pandas as pd

    pipeline = Pipeline([("m", LinearRegression())]).fit(pd.DataFrame({"a": [1, 2, 3], "b": [3, 2, 1]}), [1, 2, 3])
    with pytest.raises(ModelLoadError, match="do not match the API"):
        ModelService(pipeline, "x")


# --- options ----------------------------------------------------------------------------------


def test_options_are_read_from_the_model_itself(model_service):
    cats = model_service.options.categories
    assert cats["gender"] == ("Female", "Male")
    assert "Other" in cats["country"]
    assert "India" in cats["country"]
    assert "TikTok" in cats["most_used_platform"]
    assert model_service.options.top_countries == set(cats["country"]) - {"Other"}


# --- input handling ---------------------------------------------------------------------------


def test_country_outside_the_top_ten_becomes_other(model_service, valid_payload):
    row = model_service.prepare_row({**valid_payload, "country": "Pakistan"})
    assert row["Grouped_country"] == "Other"


@pytest.mark.parametrize("raw", ["india", "  INDIA  ", "India"])
def test_known_country_matches_ignoring_case_and_spaces(model_service, valid_payload, raw):
    assert model_service.prepare_row({**valid_payload, "country": raw})["Grouped_country"] == "India"


def test_category_match_is_case_insensitive_and_canonicalised(model_service, valid_payload):
    row = model_service.prepare_row({**valid_payload, "gender": "female", "most_used_platform": "tiktok"})
    assert row["Gender"] == "Female"
    assert row["Most_Used_Platform"] == "TikTok"


def test_unknown_categories_are_rejected_not_silently_ignored(model_service, valid_payload):
    with pytest.raises(InvalidInputError) as caught:
        model_service.prepare_row({**valid_payload, "gender": "Alien", "purpose_of_use": "Gaming"})
    assert {issue.field for issue in caught.value.issues} == {"gender", "purpose_of_use"}
    assert "Alien" not in str(caught.value)  # the submitted value is never echoed


# --- prediction -------------------------------------------------------------------------------


def test_prediction_is_a_finite_number_in_the_trained_score_range(model_service, valid_payload):
    score = model_service.predict_score(valid_payload)
    assert 3.6 <= score <= 9.4


def test_inputs_reach_the_model_in_the_right_columns(model_service, valid_payload):
    """Guards column wiring and the ordinal stress mapping: rested + calm must beat sleepless + stressed."""
    rested = model_service.predict_score(
        {**valid_payload, "sleep_hours_per_night": 9.0, "stress_level": "Low", "avg_daily_usage_hours": 2.0}
    )
    worn_out = model_service.predict_score(
        {**valid_payload, "sleep_hours_per_night": 4.0, "stress_level": "Very High", "avg_daily_usage_hours": 8.0}
    )
    assert rested > worn_out + 1.0


def test_make_prediction_adds_band_and_no_warning_for_typical_input(model_service, valid_payload):
    result = make_prediction(model_service, valid_payload)
    assert result.band in {"below_typical", "typical", "above_typical"}
    assert result.warnings == []
    assert result.model_id == model_service.model_id


def test_make_prediction_warns_about_ages_outside_the_training_data(model_service, valid_payload):
    result = make_prediction(model_service, {**valid_payload, "age": 40})
    assert any("Age (40)" in w for w in result.warnings)


# --- health -----------------------------------------------------------------------------------


def test_healthy_model_passes_the_canary(model_service):
    assert model_service.is_healthy()


def test_a_model_that_starts_failing_is_reported_unhealthy(model_path):
    service = ModelService.load(model_path, None)

    class Broken:
        def predict(self, _frame):
            raise RuntimeError("model went bad")

    service._pipeline = Broken()  # noqa: SLF001 - simulating a fault after startup
    assert service.is_healthy() is False
