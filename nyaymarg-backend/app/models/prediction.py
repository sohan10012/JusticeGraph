"""
app/models/prediction.py — Prediction history ORM model.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ARRAY, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id:                  Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id:             Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    case_type:           Mapped[str]        = mapped_column(String(50))
    court_level:         Mapped[str]        = mapped_column(String(50))
    hearing_count:       Mapped[int]        = mapped_column(Integer)
    duration_days:       Mapped[int]        = mapped_column(Integer)
    judgment_text:       Mapped[str]        = mapped_column(Text)
    predicted_outcome:   Mapped[str]        = mapped_column(String(20))    # Allowed | Dismissed
    rfc_confidence:      Mapped[float]      = mapped_column(Float)
    logreg_confidence:   Mapped[float]      = mapped_column(Float)
    ensemble_confidence: Mapped[float]      = mapped_column(Float)
    top_features:        Mapped[dict | None]= mapped_column(JSON, nullable=True)
    input_snapshot:      Mapped[dict | None]= mapped_column(JSON, nullable=True)
    created_at:          Mapped[datetime]   = mapped_column(DateTime, default=datetime.utcnow)
