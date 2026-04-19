"""
app/schemas/common.py — Shared pagination and base response schemas.
"""
from __future__ import annotations

from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated list wrapper."""
    items:       List[T]
    total:       int
    page:        int
    page_size:   int
    total_pages: int

    @classmethod
    def build(cls, items: List[T], total: int, page: int, page_size: int) -> "PaginatedResponse[T]":
        pages = (total + page_size - 1) // page_size if page_size else 1
        return cls(items=items, total=total, page=page, page_size=page_size, total_pages=pages)


class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status:    str
    version:   str
    database:  str
    models:    dict
    timestamp: str
