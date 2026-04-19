"""
app/schemas/chat.py — Chat request/response schemas (Pydantic v2).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message:    str = Field(min_length=1, max_length=2000)
    session_id: str = Field(default="default")


class ChatResponse(BaseModel):
    reply:      str
    session_id: str
    intent:     str
    cta:        Optional[dict] = None
    timestamp:  datetime


class ChatHistoryItem(BaseModel):
    id:         uuid.UUID
    role:       str
    content:    str
    intent:     Optional[str]
    cta:        Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}
