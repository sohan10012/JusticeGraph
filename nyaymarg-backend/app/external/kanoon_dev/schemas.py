"""app/external/kanoon_dev/schemas.py"""
from __future__ import annotations
from pydantic import BaseModel, Field


class KDCourt(BaseModel):
    id:   str
    name: str


class KDOrder(BaseModel):
    id:      str
    date:    str | None = None
    judges:  list[str]  = Field(default_factory=list)
    pdf_url: str | None = None
    text:    str | None = None


class KDInsightData(BaseModel):
    liberty_claim_type: str | None = None
    restraint_type:     str | None = None
    alleged_by:         str | None = None
    actual_status:      str | None = None
    reason:             str | None = None


class KDInsight(BaseModel):
    id:   str
    type: str
    data: KDInsightData = Field(default_factory=KDInsightData)
