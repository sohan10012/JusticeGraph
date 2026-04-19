"""app/external/courtlistener/schemas.py"""
from __future__ import annotations
from pydantic import BaseModel, Field


class CLOpinion(BaseModel):
    id:          int
    case_name:   str  | None = None
    date_filed:  str  | None = None
    court:       str  | None = None
    citation:    str  | None = None
    snippet:     str  | None = None
    plain_text:  str  | None = None


class CLSearchResult(BaseModel):
    count:   int             = 0
    results: list[CLOpinion] = Field(default_factory=list)


class CLJudge(BaseModel):
    id:         int
    name_full:  str | None = None
    positions:  list[dict] = Field(default_factory=list)
    education:  list[dict] = Field(default_factory=list)


class CLDocket(BaseModel):
    id:            int
    case_name:     str | None = None
    date_filed:    str | None = None
    court:         str | None = None
    parties:       list[dict] = Field(default_factory=list)
