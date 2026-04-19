"""
app/models/chat_message.py — Chat message ORM model.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id:         Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id:    Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    session_id: Mapped[str]        = mapped_column(String(50), index=True)
    role:       Mapped[str]        = mapped_column(String(10))   # user | assistant
    content:    Mapped[str]        = mapped_column(Text)
    intent:     Mapped[str | None] = mapped_column(String(30), nullable=True)
    cta:        Mapped[dict | None]= mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime]   = mapped_column(DateTime, default=datetime.utcnow)
