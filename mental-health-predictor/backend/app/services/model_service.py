"""Load, verify and run the trained scikit-learn pipeline (docs/decisions/0003)."""

from __future__ import annotations

import hashlib
import math
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.exceptions import InconsistentVersionWarning

from app.domain.exceptions import FieldIssue, InvalidInputError
from app.domain.features import (
    API_TO_MODEL_COLUMN,
    CATEGORICAL_FIELDS,
    MODEL_FEATURES,
    OTHER_COUNTRY,
    STRESS_LEVELS,
)

NOMINAL_TRANSFORMER_NAME = "Normal"  # ColumnTransformer entry name used in code.ipynb
ENCODER_STEP_NAME = "encode"
PREPROCESSOR_STEP_NAME = "preprocessor"


class ModelLoadError(RuntimeError):
    """The model file is missing, altered, incompatible or not what the API expects."""


@dataclass(frozen=True)
class ModelOptions:
    """Category values the loaded model knows, keyed by API field name."""

    categories: dict[str, tuple[str, ...]]

    @property
    def top_countries(self) -> frozenset[str]:
        return frozenset(c for c in self.categories["country"] if c != OTHER_COUNTRY)


def _sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extract_options(pipeline: Any) -> ModelOptions:
    try:
        preprocessor = pipeline.named_steps[PREPROCESSOR_STEP_NAME]
        fitted = {name: (transformer, columns) for name, transformer, columns in preprocessor.transformers_}
        encoder_pipeline, columns = fitted[NOMINAL_TRANSFORMER_NAME]
        encoder = encoder_pipeline.named_steps[ENCODER_STEP_NAME]
        by_column = {col: tuple(str(c) for c in cats) for col, cats in zip(columns, encoder.categories_, strict=True)}
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ModelLoadError(
            "The model's structure is not what this API expects (a 'preprocessor' ColumnTransformer with "
            f"a '{NOMINAL_TRANSFORMER_NAME}' one-hot step). Re-export it from code.ipynb."
        ) from exc

    categories: dict[str, tuple[str, ...]] = {}
    for api_field, column in CATEGORICAL_FIELDS.items():
        if column not in by_column:
            raise ModelLoadError(f"The model has no one-hot categories for column {column!r}.")
        categories[api_field] = tuple(sorted(by_column[column]))
    if OTHER_COUNTRY not in categories["country"]:
        raise ModelLoadError("The model's country categories do not include 'Other'.")
    return ModelOptions(categories)


class ModelService:
    def __init__(self, pipeline: Any, model_id: str) -> None:
        feature_names = getattr(pipeline, "feature_names_in_", None)
        if feature_names is None:
            raise ModelLoadError("The model was not fitted on a DataFrame, so its column names are unknown.")
        names = [str(n) for n in feature_names]
        if set(names) != MODEL_FEATURES:
            missing = sorted(MODEL_FEATURES - set(names))
            extra = sorted(set(names) - MODEL_FEATURES)
            raise ModelLoadError(f"Model columns do not match the API. Missing: {missing}. Unexpected: {extra}.")
        self._pipeline = pipeline
        self._columns = names
        self.model_id = model_id
        self.options = _extract_options(pipeline)

    @classmethod
    def load(cls, path: Path, expected_sha256: str | None) -> ModelService:
        if not path.is_file():
            raise ModelLoadError(f"Model file not found at {path}. Set MODEL_PATH to your trained .pkl file.")
        actual = _sha256_of(path)
        if expected_sha256 is not None and actual != expected_sha256.lower():
            raise ModelLoadError(
                "Model file does not match MODEL_SHA256 (file is "
                f"{actual}). It was changed or replaced; refusing to load it."
            )
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", InconsistentVersionWarning)
                pipeline = joblib.load(path)
        except InconsistentVersionWarning as warning:
            raise ModelLoadError(
                f"The model was saved with scikit-learn {warning.original_sklearn_version} but this "
                f"environment has {warning.current_sklearn_version}. Install the matching version, or "
                "re-export the model, instead of loading it with unpredictable results."
            ) from warning
        except Exception as exc:  # noqa: BLE001 - unpickling can raise almost anything; report uniformly
            raise ModelLoadError(
                f"The model file could not be loaded ({type(exc).__name__}). It may be corrupted or "
                "built with incompatible library versions."
            ) from exc
        return cls(pipeline, model_id=actual[:12])

    # -- input handling -------------------------------------------------------------------------

    def _canonical(self, field: str, value: str) -> str | None:
        lowered = value.strip().lower()
        for option in self.options.categories[field]:
            if option.lower() == lowered:
                return option
        return None

    def prepare_row(self, values: dict[str, Any]) -> dict[str, Any]:
        """Map API fields to model columns, group the country, and reject unknown categories."""
        issues: list[FieldIssue] = []
        row: dict[str, Any] = {}
        for api_field, column in API_TO_MODEL_COLUMN.items():
            row[column] = values[api_field]

        for field in ("gender", "academic_level", "most_used_platform", "purpose_of_use"):
            canonical = self._canonical(field, str(values[field]))
            if canonical is None:
                issues.append(FieldIssue(field, "Not one of the options the model knows. See /api/options."))
            else:
                row[API_TO_MODEL_COLUMN[field]] = canonical

        country = str(values["country"]).strip().lower()
        known = {c.lower(): c for c in self.options.top_countries}
        row[API_TO_MODEL_COLUMN["country"]] = known.get(country, OTHER_COUNTRY)

        if values["stress_level"] not in STRESS_LEVELS:
            issues.append(FieldIssue("stress_level", f"Must be one of: {', '.join(STRESS_LEVELS)}."))

        if issues:
            raise InvalidInputError(issues)
        return row

    def predict_score(self, values: dict[str, Any]) -> float:
        row = self.prepare_row(values)
        frame = pd.DataFrame([row], columns=self._columns)
        score = float(self._pipeline.predict(frame)[0])
        if not math.isfinite(score):
            raise RuntimeError("The model returned a non-finite value.")
        return score

    # -- health ---------------------------------------------------------------------------------

    def canary_values(self) -> dict[str, Any]:
        """A fixed, valid input built from the model's own categories. Used by the health check."""
        cats = self.options.categories
        return {
            "age": 20,
            "gender": cats["gender"][0],
            "country": OTHER_COUNTRY,
            "academic_level": cats["academic_level"][0],
            "most_used_platform": cats["most_used_platform"][0],
            "purpose_of_use": cats["purpose_of_use"][0],
            "avg_daily_usage_hours": 5.0,
            "daily_unlocks": 170,
            "study_hours": 3.0,
            "physical_activity_hours": 1.5,
            "sleep_hours_per_night": 7.0,
            "stress_level": "Medium",
        }

    def is_healthy(self) -> bool:
        try:
            return math.isfinite(self.predict_score(self.canary_values()))
        except Exception:  # noqa: BLE001 - any failure means "not healthy"
            return False
