"""app/external/ecourts/schemas.py — Pydantic v2 schemas for eCourts API responses."""
from __future__ import annotations
from pydantic import BaseModel, Field


class HearingEntry(BaseModel):
    date:      str | None = None
    purpose:   str | None = None
    next_date: str | None = None


class ECICase(BaseModel):
    cnr:                   str
    case_type:             str  | None = None
    case_number:           str  | None = None
    filing_date:           str  | None = None
    registration_date:     str  | None = None
    court:                 str  | None = None
    district:              str  | None = None
    petitioner:            str  | None = None
    respondent:            str  | None = None
    advocate_petitioner:   str  | None = None
    advocate_respondent:   str  | None = None
    status:                str  | None = None
    next_hearing_date:     str  | None = None
    hearing_history:       list[HearingEntry] = Field(default_factory=list)
    acts:                  list[str]          = Field(default_factory=list)


class CauseListEntry(BaseModel):
    cnr:      str  | None = None
    case_no:  str  | None = None
    parties:  str  | None = None
    bench:    str  | None = None


class ECICourt(BaseModel):
    code: str
    name: str
    type: str | None = None


class ECourtOrderDetail(BaseModel):
    pdf_url:       str | None = None
    markdown_text: str | None = None
