"""
app/routers/courts.py — Court endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.core.exceptions import NotFoundError
from app.schemas.common import PaginatedResponse
from app.schemas.court import CourtOut, CourtRiskRequest, CourtRiskResponse, CourtSummary
from app.services.court_service import CourtService

router  = APIRouter()
_svc    = CourtService()


@router.get("/", response_model=PaginatedResponse[CourtOut])
async def list_courts(
    state:      str | None = Query(None),
    court_type: str | None = Query(None),
    risk:       str | None = Query(None, description="low risk | moderate risk | high risk"),
    page:       int        = Query(1, ge=1),
    page_size:  int        = Query(20, ge=1, le=100),
):
    items, total = _svc.list_courts(state, court_type, risk, page, page_size)
    return PaginatedResponse.build(
        [CourtOut(**i) for i in items], total, page, page_size
    )


@router.get("/stats/summary", response_model=CourtSummary)
async def court_summary():
    return _svc.get_summary()


@router.get("/stats/risk-map")
async def risk_map():
    return _svc.get_risk_map()


@router.post("/predict-risk", response_model=CourtRiskResponse)
async def predict_court_risk(req: CourtRiskRequest):
    return _svc.predict_risk(req)


@router.get("/{court_id}", response_model=CourtOut)
async def get_court(court_id: str):
    court = _svc.get_court(court_id)
    if not court:
        raise NotFoundError("Court")
    return CourtOut(**court)


@router.get("/{court_id}/judges")
async def court_judges(court_id: str):
    return _svc.get_judges_for_court(court_id)


@router.get("/{court_id}/cases")
async def court_cases(
    court_id:  str,
    page:      int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total = _svc.get_cases_for_court(court_id, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}
