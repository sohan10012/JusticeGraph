"""
app/models/notification.py — Notification ORM model.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id:         Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id:    Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    type:       Mapped[str]        = mapped_column(String(30))   # prediction | dataset | model | system
    title:      Mapped[str]        = mapped_column(String(200))
    body:       Mapped[str]        = mapped_column(Text)
    entity_id:  Mapped[str | None] = mapped_column(String(100), nullable=True)
    action_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_read:    Mapped[bool]       = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime]   = mapped_column(DateTime, default=datetime.utcnow)
