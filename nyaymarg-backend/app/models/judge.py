"""
app/models/judge.py — Judge ORM model (mirrors df_judges schema).
"""
from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Judge(Base):
    __tablename__ = "judges"

    id:                    Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    judge_id:              Mapped[str]       = mapped_column(String(20), unique=True, index=True)  # JUDGE_0001
    judge_name:            Mapped[str]       = mapped_column(String(200))
    court_id:              Mapped[str]       = mapped_column(String(20), ForeignKey("courts.court_id"), index=True)
    court_name:            Mapped[str]       = mapped_column(String(200))
    state:                 Mapped[str]       = mapped_column(String(100), index=True)
    specialization:        Mapped[str]       = mapped_column(String(50), index=True)
    experience_years:      Mapped[int]       = mapped_column(Integer)
    cases_handled:         Mapped[int]       = mapped_column(Integer)
    avg_judgment_time_days:Mapped[int]       = mapped_column(Integer)
    reversal_rate:         Mapped[float]     = mapped_column(Float)
    bias_index:            Mapped[float]     = mapped_column(Float)
    rating_score:          Mapped[float]     = mapped_column(Float)
