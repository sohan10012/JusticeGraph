"""
app/external/indian_kanoon/schemas.py
Pydantic v2 models for Indian Kanoon API responses.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class IKDocument(BaseModel):
    tid:         int
    title:       str
    doctype:     str  | None = None
    court:       str  | None = None
    publishdate: str  | None = None
    headline:    str  | None = None


class IKSearchResult(BaseModel):
    docs:    list[IKDocument] = Field(default_factory=list)
    found:   int              = 0
    pagenum: int              = 0


class IKPrecedent(BaseModel):
    doc_id:         int
    classification: str  # Positive | Negative | Neutral


class IKStructure(BaseModel):
    facts:      list[str] = Field(default_factory=list)
    issues:     list[str] = Field(default_factory=list)
    analysis:   list[str] = Field(default_factory=list)
    conclusion: list[str] = Field(default_factory=list)


class IKDocumentMeta(BaseModel):
    title:      str
    court:      str | None = None
    date:       str | None = None
    citations:  list[str]  = Field(default_factory=list)
    ai_tags:    list[str]  = Field(default_factory=list)
    structure:  IKStructure | None = None
    precedents: list[IKPrecedent] = Field(default_factory=list)


class UnifiedSearchResult(BaseModel):
    """Normalised result from any external API source."""
    source:        str
    doc_id:        str
    title:         str
    court:         str  | None = None
    date:          str  | None = None
    outcome:       str  | None = None
    summary:       str  | None = None
    full_text_url: str  | None = None
    relevance:     float       = 0.0
    metadata:      dict[str, Any] = Field(default_factory=dict)
