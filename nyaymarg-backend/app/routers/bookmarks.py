"""
app/routers/bookmarks.py — Bookmark endpoints.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db
from app.models.bookmark import Bookmark
from app.schemas.common import PaginatedResponse
from app.schemas.notification import BookmarkCreateRequest, BookmarkOut

router = APIRouter()


@router.post("/", response_model=BookmarkOut, status_code=201)
async def add_bookmark(
    req:     BookmarkCreateRequest,
    current: dict = Depends(get_current_user),
    db:      AsyncSession = Depends(get_db),
):
    b = Bookmark(
        user_id=current["id"],
        entity_type=req.entity_type,
        entity_id=req.entity_id,
        label=req.label,
        notes=req.notes,
    )
    db.add(b)
    await db.flush()
    return BookmarkOut.model_validate(b)


@router.get("/", response_model=PaginatedResponse[BookmarkOut])
async def list_bookmarks(
    entity_type: str | None = Query(None),
    page:        int        = Query(1, ge=1),
    page_size:   int        = Query(20, ge=1, le=100),
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Bookmark).where(Bookmark.user_id == current["id"])
    if entity_type:
        stmt = stmt.where(Bookmark.entity_type == entity_type)
    stmt = stmt.order_by(Bookmark.created_at.desc())

    result   = await db.execute(stmt)
    all_bm   = result.scalars().all()
    total    = len(all_bm)
    start    = (page - 1) * page_size
    page_bm  = list(all_bm[start : start + page_size])
    return PaginatedResponse.build(
        [BookmarkOut.model_validate(b) for b in page_bm],
        total, page, page_size
    )


@router.delete("/{bookmark_id}", status_code=204)
async def delete_bookmark(
    bookmark_id: UUID,
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(Bookmark).where(Bookmark.id == bookmark_id, Bookmark.user_id == current["id"])
    )
