"""Turn a raw score into a band relative to the training data.

Bands use the quartiles of ``Mental_Health_Score`` in code.ipynb (Q1 5.1, Q3 7.1; observed range
3.6 to 9.4). They describe where an estimate sits among the survey respondents. They are not
clinical thresholds. Higher is assumed to mean better wellbeing (docs/system-design.md, question 1).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.domain.features import Limit

Band = Literal["below_typical", "typical", "above_typical"]

SCORE_SCALE = Limit(3.6, 9.4)
TYPICAL_RANGE = Limit(5.1, 7.1)

BAND_LABELS: dict[Band, str] = {
    "below_typical": "Below the typical range",
    "typical": "Within the typical range",
    "above_typical": "Above the typical range",
}

DISCLAIMER = (
    "This is a statistical estimate from a model trained on a student survey. "
    "It is not a diagnosis or medical advice. If you are struggling, talk to someone you trust "
    "or a health professional."
)


@dataclass(frozen=True)
class ScoreReading:
    score: float
    band: Band
    band_label: str


def describe_score(score: float) -> ScoreReading:
    rounded = round(score, 2)
    if rounded < TYPICAL_RANGE.min:
        band: Band = "below_typical"
    elif rounded > TYPICAL_RANGE.max:
        band = "above_typical"
    else:
        band = "typical"
    return ScoreReading(score=rounded, band=band, band_label=BAND_LABELS[band])
