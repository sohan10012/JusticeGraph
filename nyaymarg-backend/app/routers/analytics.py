"""
app/routers/analytics.py — Analytics and chart endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.core.security import get_current_user
from app.services.analytics_service import AnalyticsService
from app.services.export_service import ExportService

router   = APIRouter()
_svc     = AnalyticsService()
_exporter = ExportService()


@router.get("/overview")
async def overview():
    return _svc.overview()


@router.get("/outcomes")
async def outcomes(fmt: str = Query("json", pattern="^(json|png)$")):
    return _svc.outcomes(fmt)


@router.get("/courts")
async def court_level_chart(fmt: str = Query("json", pattern="^(json|png)$")):
    return _svc.court_level_chart(fmt)


@router.get("/duration")
async def duration_trend(fmt: str = Query("json", pattern="^(json|png)$")):
    return _svc.duration_trend(fmt)


@router.get("/case-types")
async def case_types(fmt: str = Query("json", pattern="^(json|png)$")):
    return _svc.case_types(fmt)


@router.get("/judge-performance")
async def judge_performance(fmt: str = Query("json", pattern="^(json|png)$")):
    return _svc.judge_performance(fmt)


@router.get("/state-heatmap")
async def state_heatmap(fmt: str = Query("json", pattern="^(json|png)$")):
    return _svc.state_heatmap(fmt)


@router.get("/model-performance")
async def model_performance():
    return _svc.model_performance()


@router.get("/export")
async def export_analytics_pdf(current: dict = Depends(get_current_user)):
    """Full analytics report as PDF. Requires authentication."""
    data = {
        "overview": _svc.overview(),
        "outcomes": _svc.outcomes("json"),
    }
    pdf = await _exporter.export_analytics(data)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=nyaymarg_analytics.pdf"},
    )
