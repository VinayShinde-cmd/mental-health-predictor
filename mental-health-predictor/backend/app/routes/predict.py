from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.dependencies import get_model, rate_limit
from app.domain.exceptions import InvalidInputError
from app.domain.features import FIELD_LIMITS, STRESS_LEVELS, TRAINING_RANGES
from app.domain.interpretation import DISCLAIMER, SCORE_SCALE, TYPICAL_RANGE
from app.errors import AppError
from app.schemas import OptionsResponse, PredictRequest, PredictResponse, ScoreRange
from app.services.model_service import ModelService
from app.services.prediction_service import make_prediction

router = APIRouter(prefix="/api", tags=["prediction"])


@router.get("/options", response_model=OptionsResponse, dependencies=[Depends(rate_limit("general"))])
def options(response: Response, model: ModelService = Depends(get_model)) -> OptionsResponse:  # noqa: B008
    """Dropdown values (read from the loaded model) and the numeric limits the server enforces."""
    response.headers["Cache-Control"] = "public, max-age=300"
    cats = model.options.categories
    return OptionsResponse(
        genders=list(cats["gender"]),
        academic_levels=list(cats["academic_level"]),
        platforms=list(cats["most_used_platform"]),
        purposes=list(cats["purpose_of_use"]),
        countries=list(cats["country"]),
        stress_levels=list(STRESS_LEVELS),
        limits={k: ScoreRange(min=v.min, max=v.max) for k, v in FIELD_LIMITS.items()},
        training_ranges={k: ScoreRange(min=v.min, max=v.max) for k, v in TRAINING_RANGES.items()},
    )


@router.post("/predict", response_model=PredictResponse, dependencies=[Depends(rate_limit("predict"))])
def predict(
    payload: PredictRequest,
    response: Response,
    model: ModelService = Depends(get_model),  # noqa: B008
) -> PredictResponse:
    """Estimate the score. Inputs are never stored or logged (docs/decisions/0005)."""
    response.headers["Cache-Control"] = "no-store"
    try:
        result = make_prediction(model, payload.model_dump())
    except InvalidInputError as exc:
        raise AppError(
            400,
            "invalid_request",
            "Some fields are invalid.",
            details=[{"field": i.field, "message": i.message} for i in exc.issues],
        ) from exc
    return PredictResponse(
        score=result.score,
        band=result.band,
        band_label=result.band_label,
        typical_range=ScoreRange(min=TYPICAL_RANGE.min, max=TYPICAL_RANGE.max),
        scale=ScoreRange(min=SCORE_SCALE.min, max=SCORE_SCALE.max),
        warnings=result.warnings,
        disclaimer=DISCLAIMER,
        model_id=result.model_id,
    )
