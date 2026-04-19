"""
app/models/bookmark.py
app/models/notification.py
app/models/chat_message.py
app/models/ml_model.py
app/models/dataset.py
app/models/audit_log.py
"""
# ─── bookmark.py ──────────────────────────────────────────────────────────────
from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class Bookmark(Base):
    __tablename__ = "bookmarks"
    id:          Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id:     Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    entity_type: Mapped[str]        = mapped_column(String(20))   # case | prediction | judge | court | search
    entity_id:   Mapped[str]        = mapped_column(String(100))
    label:       Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes:       Mapped[str | None] = mapped_column(Text, nullable=True)
    meta:        Mapped[dict | None]= mapped_column(JSON, nullable=True)
    created_at:  Mapped[datetime]   = mapped_column(DateTime, default=datetime.utcnow)
