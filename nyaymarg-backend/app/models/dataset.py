"""
app/models/dataset.py — Uploaded dataset registry ORM model.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id:          Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id:     Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    name:        Mapped[str]        = mapped_column(String(200))
    filename:    Mapped[str]        = mapped_column(String(300))
    file_path:   Mapped[str]        = mapped_column(String(500))
    file_size:   Mapped[int]        = mapped_column(Integer)    # bytes
    row_count:   Mapped[int | None] = mapped_column(Integer, nullable=True)
    status:      Mapped[str]        = mapped_column(String(20), default="pending")  # pending | processing | ready | failed
    schema_info: Mapped[dict | None]= mapped_column(JSON, nullable=True)
    error_msg:   Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at:  Mapped[datetime]   = mapped_column(DateTime, default=datetime.utcnow)
    processed_at:Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
