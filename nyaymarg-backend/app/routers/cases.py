"""
app/routers/cases.py — Case endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.exceptions import NotFoundError
from app.core.security import get_current_user, require_role
from app.models.user import UserRole
import uuid, datetime
from app.database import get_db
from app.schemas.case import CaseCreateRequest, CaseOut, CaseUpdateRequest
from app.schemas.common import PaginatedResponse
from app.services.case_service import CaseService

router = APIRouter()
_svc   = CaseService()


@router.get("/", response_model=PaginatedResponse[CaseOut])
async def list_cases(
    case_type: str | None = Query(None),
    status:    str | None = Query(None),
    state:     str | None = Query(None),
    court_id:  str | None = Query(None),
    page:      int        = Query(1, ge=1),
    page_size: int        = Query(20, ge=1, le=100),
):
    items, total = _svc.list_cases(case_type, status, state, court_id, page, page_size)
    return PaginatedResponse.build(
        [CaseOut(**i) for i in items], total, page, page_size
    )


@router.get("/stats/summary")
async def case_summary():
    return _svc.get_summary()


@router.get("/stats/pendency")
async def pendency():
    return _svc.pendency_distribution()


@router.get("/search")
async def search_cases(
    q:         str = Query(..., min_length=2),
    page:      int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total = _svc.search(q, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size, "query": q}


@router.get("/{case_id}", response_model=CaseOut)
async def get_case(case_id: str):
    c = _svc.get_case(case_id)
    if not c:
        raise NotFoundError("Case")
    return CaseOut(**c)


@router.post("/", response_model=CaseOut, status_code=201,
             dependencies=[require_role(UserRole.researcher, UserRole.admin)])
async def create_case(body: CaseCreateRequest, db=Depends(get_db)):
    """Researcher/Admin: add a new case to the database."""
    from app.models.case import Case
    import uuid, datetime
    c = Case(
        id=uuid.uuid4(),
        case_id=f"CASE_{uuid.uuid4().hex[:6].upper()}",
        case_title=body.case_title,
        case_number=body.case_number,
        court_id=body.court_id,
        court_name="",
        state="",
        judge_id=body.judge_id,
        case_type=body.case_type,
        status=body.status,
        filing_date=body.filing_date,
        hearing_count=body.hearing_count,
        complexity_score=body.complexity_score,
        case_value_lakhs=body.case_value_lakhs,
        days_pending=body.days_pending,
        public_interest=body.public_interest,
        law_id=body.law_id,
        outcome=0,
        judgment_text=body.judgment_text,
    )
    db.add(c)
    await db.flush()
    return CaseOut.model_validate(c)
