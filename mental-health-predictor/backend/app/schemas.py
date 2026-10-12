"""Request and response models. Limits come from domain.features so the frontend can mirror them."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.features import FIELD_LIMITS as L
from app.domain.interpretation import Band

StressLevel = Literal["Low", "Medium", "High", "Very High"]


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    age: int = Field(ge=L["age"].min, le=L["age"].max)
    gender: str = Field(min_length=1, max_length=40)
    country: str = Field(min_length=1, max_length=80)
    academic_level: str = Field(min_length=1, max_length=40)
    most_used_platform: str = Field(min_length=1, max_length=40)
    purpose_of_use: str = Field(min_length=1, max_length=40)
    avg_daily_usage_hours: float = Field(
        ge=L["avg_daily_usage_hours"].min, le=L["avg_daily_usage_hours"].max, allow_inf_nan=False
    )
    daily_unlocks: int = Field(ge=L["daily_unlocks"].min, le=L["daily_unlocks"].max)
    study_hours: float = Field(ge=L["study_hours"].min, le=L["study_hours"].max, allow_inf_nan=False)
    physical_activity_hours: float = Field(
        ge=L["physical_activity_hours"].min, le=L["physical_activity_hours"].max, allow_inf_nan=False
    )
    sleep_hours_per_night: float = Field(
        ge=L["sleep_hours_per_night"].min, le=L["sleep_hours_per_night"].max, allow_inf_nan=False
    )
    stress_level: StressLevel


class ScoreRange(BaseModel):
    min: float
    max: float


class PredictResponse(BaseModel):
    score: float
    band: Band
    band_label: str
    typical_range: ScoreRange
    scale: ScoreRange
    warnings: list[str]
    disclaimer: str
    model_id: str


class OptionsResponse(BaseModel):
    genders: list[str]
    academic_levels: list[str]
    platforms: list[str]
    purposes: list[str]
    countries: list[str]
    stress_levels: list[str]
    limits: dict[str, ScoreRange]
    training_ranges: dict[str, ScoreRange]


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    components: dict[str, Literal["ok", "failed"]] | None = None
