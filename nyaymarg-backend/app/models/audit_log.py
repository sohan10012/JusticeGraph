"""
app/models/audit_log.py — Audit log ORM model (writes on every mutating action).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id:          Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id:     Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    action:      Mapped[str]        = mapped_column(String(100), index=True)  # e.g. "user.register"
    resource:    Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip_address:  Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent:  Mapped[str | None] = mapped_column(String(300), nullable=True)
    payload:     Mapped[dict | None]= mapped_column(JSON, nullable=True)
    created_at:  Mapped[datetime]   = mapped_column(DateTime, default=datetime.utcnow)
