"""
app/routers/predictions.py — Prediction endpoints.
"""
from __future__ import annotations

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.security import detect_pii, get_current_user
from app.core.exceptions import PIIDetectedError
from app.database import get_db
from app.models.prediction import Prediction
from app.schemas.common import PaginatedResponse
from app.schemas.prediction import (
    BatchPredictionRequest,
    PredictionHistoryItem,
    PredictionRequest,
    PredictionResponse,
)
from app.services.export_service import ExportService
from app.services.prediction_service import PredictionService

router   = APIRouter()
_svc     = PredictionService()
_exporter = ExportService()


@router.post("/", response_model=PredictionResponse, status_code=201)
async def predict(
    req:     PredictionRequest,
    current: dict = Depends(get_current_user),
    db:      AsyncSession = Depends(get_db),
):
    """Single case outcome prediction — requires authentication."""
    if detect_pii(req.judgment_text):
        raise PIIDetectedError()
    return await _svc.predict_case_outcome(req, current["id"], db)


@router.post("/batch", response_model=list[PredictionResponse])
async def predict_batch(
    req:     BatchPredictionRequest,
    current: dict = Depends(get_current_user),
    db:      AsyncSession = Depends(get_db),
):
    """Batch prediction (up to 1000 cases)."""
    return await _svc.predict_batch(req.cases, current["id"], db)


@router.post("/court-risk")
async def predict_court_risk(req):
    """Wraps court backlog RF prediction (convenience alias)."""
    from app.services.court_service import CourtService
    from app.schemas.court import CourtRiskRequest
    return CourtService().predict_risk(CourtRiskRequest(**req.model_dump()))


@router.get("/history", response_model=PaginatedResponse[PredictionHistoryItem])
async def prediction_history(
    page:      int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current:   dict = Depends(get_current_user),
    db:        AsyncSession = Depends(get_db),
):
    stmt = (
        select(Prediction)
        .where(Prediction.user_id == current["id"])
        .order_by(Prediction.created_at.desc())
    )
    result = await db.execute(stmt)
    all_p  = result.scalars().all()
    total  = len(all_p)
    start  = (page - 1) * page_size
    page_items = list(all_p[start : start + page_size])
    return PaginatedResponse.build(
        [PredictionHistoryItem.model_validate(p) for p in page_items],
        total, page, page_size
    )


@router.get("/export/{prediction_id}")
async def export_prediction(
    prediction_id: UUID,
    current: dict  = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Prediction).where(
            Prediction.id == prediction_id,
            Prediction.user_id == current["id"]
        )
    )
    pred = result.scalar_one_or_none()
    if not pred:
        raise NotFoundError("Prediction")

    pdf = await _exporter.export_prediction({
        "predicted_outcome":   pred.predicted_outcome,
        "ensemble_confidence": pred.ensemble_confidence,
        "rfc_confidence":      pred.rfc_confidence,
        "logreg_confidence":   pred.logreg_confidence,
        "top_features":        pred.top_features or [],
    })
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=prediction_{prediction_id}.pdf"},
    )


@router.get("/{prediction_id}", response_model=PredictionHistoryItem)
async def get_prediction(
    prediction_id: UUID,
    current: dict  = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Prediction).where(
            Prediction.id == prediction_id,
            Prediction.user_id == current["id"]
        )
    )
    pred = result.scalar_one_or_none()
    if not pred:
        raise NotFoundError("Prediction")
    return PredictionHistoryItem.model_validate(pred)


@router.delete("/{prediction_id}", status_code=204)
async def delete_prediction(
    prediction_id: UUID,
    current: dict  = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import delete
    await db.execute(
        delete(Prediction).where(
            Prediction.id == prediction_id,
            Prediction.user_id == current["id"]
        )
    )
