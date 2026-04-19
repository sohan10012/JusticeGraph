"""
app/schemas/case.py — Case request/response schemas (Pydantic v2).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class CaseOut(BaseModel):
    case_id:          str
    case_title:       str
    case_number:      str
    court_id:         str
    court_name:       str
    state:            str
    judge_id:         str
    case_type:        str
    status:           str
    filing_date:      Optional[date]
    hearing_count:    int
    complexity_score: float
    case_value_lakhs: float
    days_pending:     int
    public_interest:  bool
    law_id:           str
    outcome:          int

    model_config = {"from_attributes": True}


class CaseCreateRequest(BaseModel):
    case_title:       str  = Field(min_length=5, max_length=500)
    case_number:      str
    court_id:         str
    judge_id:         str
    case_type:        str
    status:           str  = "Pending"
    filing_date:      Optional[date] = None
    hearing_count:    int  = Field(ge=0, default=0)
    complexity_score: float= Field(ge=0, le=10, default=5.0)
    case_value_lakhs: float= Field(ge=0, default=0.0)
    days_pending:     int  = Field(ge=0, default=0)
    public_interest:  bool = False
    law_id:           str
    judgment_text:    Optional[str] = None


class CaseUpdateRequest(BaseModel):
    status:           Optional[str]  = None
    hearing_count:    Optional[int]  = None
    days_pending:     Optional[int]  = None
    judgment_text:    Optional[str]  = None


class CaseSearchResult(BaseModel):
    case_id:    str
    case_title: str
    case_type:  str
    court_name: str
    state:      str
    status:     str
    score:      float = 1.0    # relevance score (TF-IDF for /search, cosine for /similar)
