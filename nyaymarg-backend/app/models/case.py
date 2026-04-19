"""
app/models/case.py — Case ORM model (mirrors df_cases + NyayMarg fields).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import ARRAY, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Case(Base):
    __tablename__ = "cases"

    id:               Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id:          Mapped[str]       = mapped_column(String(20), unique=True, index=True)
    case_title:       Mapped[str]       = mapped_column(String(500))
    case_number:      Mapped[str]       = mapped_column(String(50))
    court_id:         Mapped[str]       = mapped_column(String(20), ForeignKey("courts.court_id"), index=True)
    court_name:       Mapped[str]       = mapped_column(String(200))
    state:            Mapped[str]       = mapped_column(String(100), index=True)
    judge_id:         Mapped[str]       = mapped_column(String(20), ForeignKey("judges.judge_id"), index=True)
    case_type:        Mapped[str]       = mapped_column(String(50), index=True)
    status:           Mapped[str]       = mapped_column(String(30), index=True)
    filing_date:      Mapped[date | None] = mapped_column(Date, nullable=True)
    hearing_count:    Mapped[int]       = mapped_column(Integer)
    complexity_score: Mapped[float]     = mapped_column(Float)
    case_value_lakhs: Mapped[float]     = mapped_column(Float)
    days_pending:     Mapped[int]       = mapped_column(Integer)
    public_interest:  Mapped[bool]      = mapped_column(Boolean, default=False)
    law_id:           Mapped[str]       = mapped_column(String(20), index=True)
    outcome:          Mapped[int]       = mapped_column(Integer)  # 1=Decided, 0=other
    judgment_text:    Mapped[str | None]= mapped_column(Text, nullable=True)
    created_at:       Mapped[datetime]  = mapped_column(DateTime, default=datetime.utcnow)
