"""
app/models/ml_model.py — ML model version registry ORM model.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MLModelVersion(Base):
    __tablename__ = "ml_model_versions"

    id:             Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_tag:    Mapped[str]        = mapped_column(String(50), unique=True)   # e.g. "v2024-04-19T10:00"
    rf_accuracy:    Mapped[float]      = mapped_column(Float)
    rf_cv_f1:       Mapped[float]      = mapped_column(Float)
    lr_accuracy:    Mapped[float]      = mapped_column(Float)
    lr_f1:          Mapped[float]      = mapped_column(Float)
    lr_auc_roc:     Mapped[float]      = mapped_column(Float)
    is_active:      Mapped[bool]       = mapped_column(Boolean, default=False)
    metrics:        Mapped[dict | None]= mapped_column(JSON, nullable=True)
    artefact_path:  Mapped[str | None] = mapped_column(String(500), nullable=True)
    triggered_by:   Mapped[str | None] = mapped_column(String(100), nullable=True)
    trained_at:     Mapped[datetime]   = mapped_column(DateTime, default=datetime.utcnow)
