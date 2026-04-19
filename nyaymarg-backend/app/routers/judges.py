"""
app/routers/judges.py — Judge endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.exceptions import NotFoundError
from app.schemas.common import PaginatedResponse
from app.schemas.judge import JudgeLeaderboardEntry, JudgeOut
from app.services.judge_service import JudgeService

router = APIRouter()
_svc   = JudgeService()


@router.get("/", response_model=PaginatedResponse[JudgeOut])
async def list_judges(
    state:          str | None = Query(None),
    specialization: str | None = Query(None),
    page:           int        = Query(1, ge=1),
    page_size:      int        = Query(20, ge=1, le=100),
):
    items, total = _svc.list_judges(state, specialization, page, page_size)
    return PaginatedResponse.build(
        [JudgeOut(**i) for i in items], total, page, page_size
    )


@router.get("/leaderboard")
async def leaderboard(top_n: int = Query(20, ge=1, le=50)):
    return _svc.leaderboard(top_n)


@router.get("/stats/bias-analysis")
async def bias_analysis():
    return _svc.bias_analysis()


@router.get("/stats/performance")
async def performance_stats():
    return _svc.performance_stats()


@router.get("/{judge_id}", response_model=JudgeOut)
async def get_judge(judge_id: str):
    j = _svc.get_judge(judge_id)
    if not j:
        raise NotFoundError("Judge")
    return JudgeOut(**j)


@router.get("/{judge_id}/cases")
async def judge_cases(
    judge_id:  str,
    page:      int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total = _svc.get_cases_for_judge(judge_id, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}
