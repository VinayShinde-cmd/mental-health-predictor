"""Shared fixtures.

The model used in tests is the SYNTHETIC pipeline from scripts/make_dev_model.py: the same structure as
the notebook's pipeline, trained on random data. It exercises our loading, validation and prediction code
for real (nothing about scikit-learn is mocked); it says nothing about the quality of the real model.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pytest

from app.services.model_service import ModelService
from scripts.make_dev_model import build_dev_pipeline, synthetic_frame


@pytest.fixture(scope="session")
def model_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("model") / "dev_model.pkl"
    features, target = synthetic_frame()
    joblib.dump(build_dev_pipeline().fit(features, target), path)
    return path


@pytest.fixture(scope="session")
def model_service(model_path: Path) -> ModelService:
    return ModelService.load(model_path, None)


@pytest.fixture
def valid_payload() -> dict[str, Any]:
    return {
        "age": 21,
        "gender": "Female",
        "country": "India",
        "academic_level": "Undergraduate",
        "most_used_platform": "Instagram",
        "purpose_of_use": "Entertainment",
        "avg_daily_usage_hours": 4.5,
        "daily_unlocks": 150,
        "study_hours": 3.0,
        "physical_activity_hours": 1.5,
        "sleep_hours_per_night": 7.0,
        "stress_level": "Medium",
    }
