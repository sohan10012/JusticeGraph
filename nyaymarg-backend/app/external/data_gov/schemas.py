"""app/external/data_gov/schemas.py"""
from __future__ import annotations
from pydantic import BaseModel, Field


class CourtInfraRecord(BaseModel):
    state:         str
    courts:        int   | None = None
    judges:        int   | None = None
    pending_cases: int   | None = None
    disposal_rate: float | None = None


class PendencyRecord(BaseModel):
    state:      str
    court_type: str  | None = None
    pending:    int  | None = None
    year:       int  | None = None


class DataGovResponse(BaseModel):
    total:   int               = 0
    records: list[dict]        = Field(default_factory=list)
