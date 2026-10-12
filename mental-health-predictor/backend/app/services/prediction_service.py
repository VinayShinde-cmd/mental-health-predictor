"""Combine a raw model score with interpretation and warnings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.features import training_range_warnings
from app.domain.interpretation import Band, describe_score
from app.services.model_service import ModelService


@dataclass(frozen=True)
class Prediction:
    score: float
    band: Band
    band_label: str
    warnings: list[str]
    model_id: str


def make_prediction(model: ModelService, values: dict[str, Any]) -> Prediction:
    """Raises InvalidInputError for categories the model does not know."""
    raw = model.predict_score(values)
    reading = describe_score(raw)
    numeric = {k: float(v) for k, v in values.items() if isinstance(v, int | float) and not isinstance(v, bool)}
    return Prediction(
        score=reading.score,
        band=reading.band,
        band_label=reading.band_label,
        warnings=training_range_warnings(numeric),
        model_id=model.model_id,
    )
