"""
app/schemas/prediction.py — Prediction request/response schemas (Pydantic v2).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    case_type:     str
    court_level:   str  = "District Court"
    hearing_count: int  = Field(ge=0, default=5)
    duration_days: int  = Field(ge=0, default=180)
    judgment_text: str  = Field(min_length=10)
    keywords:      list[str] = Field(default_factory=list)


class BatchPredictionRequest(BaseModel):
    cases: list[PredictionRequest] = Field(max_length=1000)


class PredictionResponse(BaseModel):
    prediction_id:       uuid.UUID
    predicted_outcome:   str          # Allowed | Dismissed
    rfc_confidence:      float
    logreg_confidence:   float
    ensemble_confidence: float
    top_features:        list[dict]
    similar_cases_count: int = 0
    analyzed_at:         datetime


class PredictionHistoryItem(BaseModel):
    id:                  uuid.UUID
    case_type:           str
    court_level:         str
    predicted_outcome:   str
    ensemble_confidence: float
    created_at:          datetime

    model_config = {"from_attributes": True}


class CourtRiskPredictRequest(BaseModel):
    judge_strength:         int   = Field(ge=1)
    pending_cases:          int   = Field(ge=0)
    monthly_filing_rate:    int   = Field(ge=1)
    monthly_disposal_rate:  int   = Field(ge=1)
    avg_disposal_time_days: int   = Field(ge=1)
    infrastructure_score:   float = Field(ge=0, le=10)
    digitization_level:     float = Field(ge=0, le=1)
