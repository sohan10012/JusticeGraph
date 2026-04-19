"""
app/routers/notifications.py — Notification endpoints.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.notification import NotificationOut, UnreadCountResponse
from app.services.notification_service import NotificationService

router = APIRouter()
_svc   = NotificationService()


@router.get("/", response_model=PaginatedResponse[NotificationOut])
async def list_notifications(
    unread_only: bool = Query(False),
    page:        int  = Query(1, ge=1),
    page_size:   int  = Query(20, ge=1, le=100),
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await _svc.list_for_user(db, current["id"], unread_only, page, page_size)
    return PaginatedResponse.build(
        [NotificationOut.model_validate(n) for n in items],
        total, page, page_size
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await _svc.unread_count(db, current["id"])
    return UnreadCountResponse(count=count)


@router.put("/{notification_id}/read", status_code=204)
async def mark_read(
    notification_id: UUID,
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _svc.mark_read(db, notification_id)


@router.put("/read-all", status_code=204)
async def mark_all_read(
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _svc.mark_all_read(db, current["id"])


@router.delete("/{notification_id}", status_code=204)
async def delete_notification(
    notification_id: UUID,
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _svc.delete(db, notification_id)
