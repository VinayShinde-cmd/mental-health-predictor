from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse

from app.dependencies import get_model
from app.schemas import HealthResponse
from app.services.model_service import ModelService

router = APIRouter(prefix="/api", tags=["health"])

NO_STORE = {"Cache-Control": "no-store"}


@router.get("/health/live", response_model=HealthResponse)
def live(response: Response) -> HealthResponse:
    """Process is up. Cheap; for the load balancer. Does not touch the model."""
    response.headers.update(NO_STORE)
    return HealthResponse(status="ok")


@router.get("/health", response_model=HealthResponse)
def health(model: ModelService = Depends(get_model)) -> JSONResponse:  # noqa: B008
    """Readiness: the model is loaded and answers a fixed test input with a finite number."""
    ok = model.is_healthy()
    body = HealthResponse(status="ok" if ok else "degraded", components={"model": "ok" if ok else "failed"})
    return JSONResponse(status_code=200 if ok else 503, content=body.model_dump(), headers=NO_STORE)
