"""
app/schemas/court.py — Court request/response schemas (Pydantic v2).
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CourtOut(BaseModel):
    court_id:              str
    court_name:            str
    city:                  str
    state:                 str
    court_type:            str
    judge_strength:        int
    pending_cases:         int
    monthly_filing_rate:   int
    monthly_disposal_rate: int
    avg_disposal_time_days:int
    infrastructure_score:  float
    digitization_level:    float
    backlog_rate:          Optional[float] = None
    utilization_rate:      Optional[float] = None
    efficiency_score:      Optional[float] = None
    backlog_risk_score:    Optional[float] = None
    risk_category:         Optional[str]   = None

    model_config = {"from_attributes": True}


class CourtSummary(BaseModel):
    total_courts:    int
    by_risk_category:dict
    by_state:        dict
    by_court_type:   dict


class CourtRiskRequest(BaseModel):
    judge_strength:         int   = Field(ge=1)
    pending_cases:          int   = Field(ge=0)
    monthly_filing_rate:    int   = Field(ge=1)
    monthly_disposal_rate:  int   = Field(ge=1)
    avg_disposal_time_days: int   = Field(ge=1)
    infrastructure_score:   float = Field(ge=0, le=10)
    digitization_level:     float = Field(ge=0, le=1)


class CourtRiskResponse(BaseModel):
    risk_label:           str    # Low Risk | Moderate Risk | High Risk
    risk_probability:     float
    risk_score:           float
    contributing_factors: list[dict]
