"""The 12 model inputs, the limits the API enforces, and the ranges the model was trained on.

Training ranges come from ``df.describe()`` in code.ipynb (5,000 rows). Physical activity has its
negative values clipped to 0 in the notebook, so its trained range starts at 0.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Limit:
    min: float
    max: float


# What the API accepts. Wider than the training data on purpose: plausible people outside the
# training range get a warning instead of an error. The frontend reads these from /api/options so
# client-side checks match the server.
FIELD_LIMITS: dict[str, Limit] = {
    "age": Limit(13, 100),
    "avg_daily_usage_hours": Limit(0, 24),
    "daily_unlocks": Limit(0, 2000),
    "study_hours": Limit(0, 24),
    "physical_activity_hours": Limit(0, 24),
    "sleep_hours_per_night": Limit(0, 24),
}

# Observed in the training data (min, max).
TRAINING_RANGES: dict[str, Limit] = {
    "age": Limit(18, 24),
    "avg_daily_usage_hours": Limit(1.0, 8.8),
    "daily_unlocks": Limit(62, 273),
    "study_hours": Limit(0.3, 8.3),
    "physical_activity_hours": Limit(0.0, 4.1),
    "sleep_hours_per_night": Limit(3.6, 9.9),
}

FIELD_LABELS: dict[str, str] = {
    "age": "Age",
    "avg_daily_usage_hours": "Daily phone use",
    "daily_unlocks": "Daily unlocks",
    "study_hours": "Study hours",
    "physical_activity_hours": "Physical activity",
    "sleep_hours_per_night": "Sleep",
}

STRESS_LEVELS: tuple[str, ...] = ("Low", "Medium", "High", "Very High")
OTHER_COUNTRY = "Other"

# API field name -> column name the pipeline was trained with.
API_TO_MODEL_COLUMN: dict[str, str] = {
    "age": "Age",
    "gender": "Gender",
    "country": "Grouped_country",
    "academic_level": "Academic_Level",
    "most_used_platform": "Most_Used_Platform",
    "purpose_of_use": "Purpose_Of_Use",
    "avg_daily_usage_hours": "Avg_Daily_Usage_Hours",
    "daily_unlocks": "Daily_Unlocks",
    "study_hours": "Study_Hours",
    "physical_activity_hours": "Physical_Activity_Hours",
    "sleep_hours_per_night": "Sleep_Hours_Per_Night",
    "stress_level": "Stress_Level",
}
MODEL_FEATURES: frozenset[str] = frozenset(API_TO_MODEL_COLUMN.values())

# API field -> the model's nominal (one-hot) column it must match.
CATEGORICAL_FIELDS: dict[str, str] = {
    "gender": "Gender",
    "academic_level": "Academic_Level",
    "most_used_platform": "Most_Used_Platform",
    "purpose_of_use": "Purpose_Of_Use",
    "country": "Grouped_country",
}


def _fmt(number: float) -> str:
    return f"{number:g}"


def training_range_warnings(values: dict[str, float]) -> list[str]:
    """Plain-language warnings for numeric inputs outside what the model has seen."""
    warnings: list[str] = []
    for field, rng in TRAINING_RANGES.items():
        value = values.get(field)
        if value is None:
            continue
        if value < rng.min or value > rng.max:
            warnings.append(
                f"{FIELD_LABELS[field]} ({_fmt(value)}) is outside the {_fmt(rng.min)} to "
                f"{_fmt(rng.max)} range the model was trained on, so this estimate is less reliable."
            )
    return warnings
