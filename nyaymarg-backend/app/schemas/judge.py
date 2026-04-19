"""
app/schemas/judge.py — Judge request/response schemas (Pydantic v2).
"""
from __future__ import annotations

from pydantic import BaseModel


class JudgeOut(BaseModel):
    judge_id:               str
    judge_name:             str
    court_id:               str
    court_name:             str
    state:                  str
    specialization:         str
    experience_years:       int
    cases_handled:          int
    avg_judgment_time_days: int
    reversal_rate:          float
    bias_index:             float
    rating_score:           float

    model_config = {"from_attributes": True}


class JudgeLeaderboardEntry(BaseModel):
    rank:        int
    judge_id:    str
    judge_name:  str
    court_name:  str
    state:       str
    rating_score:float
    cases_handled:int
    reversal_rate:float
