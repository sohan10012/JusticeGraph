"""
app/services/notification_service.py — Notification CRUD service.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationService:

    async def create(
        self,
        db:         AsyncSession,
        user_id:    uuid.UUID,
        type:       str,
        title:      str,
        body:       str,
        entity_id:  str | None = None,
        action_url: str | None = None,
    ) -> Notification:
        n = Notification(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            entity_id=entity_id,
            action_url=action_url,
        )
        db.add(n)
        await db.flush()
        return n

    async def list_for_user(
        self,
        db:          AsyncSession,
        user_id:     uuid.UUID,
        unread_only: bool = False,
        page:        int = 1,
        page_size:   int = 20,
    ) -> tuple[list[Notification], int]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        stmt = stmt.order_by(Notification.created_at.desc())

        result = await db.execute(stmt)
        all_items = result.scalars().all()
        total     = len(all_items)
        start     = (page - 1) * page_size
        return list(all_items[start : start + page_size]), total

    async def unread_count(self, db: AsyncSession, user_id: uuid.UUID) -> int:
        from sqlalchemy import func
        from sqlalchemy import select as sel
        stmt   = sel(func.count()).select_from(Notification).where(
            Notification.user_id == user_id, Notification.is_read.is_(False)
        )
        result = await db.execute(stmt)
        return int(result.scalar() or 0)

    async def mark_read(self, db: AsyncSession, notification_id: uuid.UUID) -> None:
        await db.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(is_read=True)
        )

    async def mark_all_read(self, db: AsyncSession, user_id: uuid.UUID) -> None:
        await db.execute(
            update(Notification)
            .where(Notification.user_id == user_id)
            .values(is_read=True)
        )

    async def delete(self, db: AsyncSession, notification_id: uuid.UUID) -> None:
        from sqlalchemy import delete
        await db.execute(
            delete(Notification).where(Notification.id == notification_id)
        )
