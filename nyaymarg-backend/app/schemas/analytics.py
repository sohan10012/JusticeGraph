"""
app/schemas/analytics.py — Analytics response schemas (Pydantic v2).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class OverviewStats(BaseModel):
    total_courts:    int
    total_judges:    int
    total_cases:     int
    pending_cases:   int
    decided_cases:   int
    high_risk_courts:int
    avg_pending_days:float
    prediction_count:int


class ChartDataPoint(BaseModel):
    label: str
    value: Any


class ChartResponse(BaseModel):
    title: str
    data:  list[ChartDataPoint]
    chart_type: str = "bar"


class ModelPerformance(BaseModel):
    rf_model:  dict
    lr_model:  dict
    ensemble:  dict
    trained_at:str | None = None
