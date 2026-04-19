"""
app/models/court.py — Court ORM model (mirrors df_courts schema).
"""
from __future__ import annotations

import uuid

from sqlalchemy import Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Court(Base):
    __tablename__ = "courts"

    id:                    Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    court_id:              Mapped[str]       = mapped_column(String(20), unique=True, index=True)  # COURT_001
    court_name:            Mapped[str]       = mapped_column(String(200))
    city:                  Mapped[str]       = mapped_column(String(100))
    state:                 Mapped[str]       = mapped_column(String(100), index=True)
    court_type:            Mapped[str]       = mapped_column(String(50), index=True)
    judge_strength:        Mapped[int]       = mapped_column(Integer)
    pending_cases:         Mapped[int]       = mapped_column(Integer)
    monthly_filing_rate:   Mapped[int]       = mapped_column(Integer)
    monthly_disposal_rate: Mapped[int]       = mapped_column(Integer)
    avg_disposal_time_days:Mapped[int]       = mapped_column(Integer)
    infrastructure_score:  Mapped[float]     = mapped_column(Float)
    digitization_level:    Mapped[float]     = mapped_column(Float)
    backlog_rate:          Mapped[float | None] = mapped_column(Float, nullable=True)
    utilization_rate:      Mapped[float | None] = mapped_column(Float, nullable=True)
    efficiency_score:      Mapped[float | None] = mapped_column(Float, nullable=True)
    backlog_risk_score:    Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_category:         Mapped[str | None]   = mapped_column(String(20), nullable=True)  # Low/Moderate/High Risk
