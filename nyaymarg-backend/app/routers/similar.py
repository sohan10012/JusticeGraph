"""
app/routers/similar.py — Precedent / similarity search endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas.notification import SimilarCase, SimilaritySearchRequest
from app.services.similarity_service import SimilarityService

router = APIRouter()
_svc   = SimilarityService()


@router.post("/search", response_model=list[SimilarCase])
async def search_similar(req: SimilaritySearchRequest):
    return _svc.search(
        req.query,
        top_n=req.top_n,
        court_filter=req.court_filter,
        outcome_filter=req.outcome_filter,
    )


@router.get("/cases")
async def list_indexed_cases(
    page:      int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    from app.data.seed import get_registry
    df    = get_registry().df_cases
    total = len(df)
    start = (page - 1) * page_size
    chunk = df.iloc[start : start + page_size]
    return {"items": chunk.to_dict(orient="records"), "total": total, "page": page}


@router.get("/cases/{case_id}")
async def get_indexed_case(case_id: str):
    from app.data.seed import get_registry
    from app.core.exceptions import NotFoundError
    df  = get_registry().df_cases
    row = df[df["case_id"] == case_id]
    if row.empty:
        raise NotFoundError("Case")
    return row.iloc[0].to_dict()
