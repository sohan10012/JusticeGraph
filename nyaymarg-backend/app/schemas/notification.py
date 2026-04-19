"""
app/schemas/notification.py — Notification schemas (Pydantic v2).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id:         uuid.UUID
    type:       str
    title:      str
    body:       str
    entity_id:  Optional[str]
    action_url: Optional[str]
    is_read:    bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UnreadCountResponse(BaseModel):
    count: int


# ── Dataset schemas ────────────────────────────────────────────────────────────
class DatasetOut(BaseModel):
    id:           uuid.UUID
    name:         str
    filename:     str
    file_size:    int
    row_count:    Optional[int]
    status:       str
    schema_info:  Optional[dict]
    error_msg:    Optional[str]
    created_at:   datetime
    processed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class DatasetStatusResponse(BaseModel):
    id:     uuid.UUID
    status: str
    error:  Optional[str]


# ── Bookmark schemas ───────────────────────────────────────────────────────────
class BookmarkCreateRequest(BaseModel):
    entity_type: str   # case | prediction | judge | court | search
    entity_id:   str
    label:       Optional[str] = None
    notes:       Optional[str] = None


class BookmarkOut(BaseModel):
    id:          uuid.UUID
    entity_type: str
    entity_id:   str
    label:       Optional[str]
    notes:       Optional[str]
    created_at:  datetime

    model_config = {"from_attributes": True}


# ── Similar case ───────────────────────────────────────────────────────────────
class SimilarCase(BaseModel):
    case_id:          str
    case_title:       str
    case_type:        str
    court_name:       str
    state:            str
    outcome_label:    str
    similarity_score: float
    filing_date:      Optional[str]


class SimilaritySearchRequest(BaseModel):
    query:          str
    top_n:          int = 5
    court_filter:   Optional[str] = None
    outcome_filter: Optional[str] = None   # Decided | Pending


# ── ML Model schemas ───────────────────────────────────────────────────────────
class MLModelVersionOut(BaseModel):
    id:           uuid.UUID
    version_tag:  str
    rf_accuracy:  float
    rf_cv_f1:     float
    lr_accuracy:  float
    lr_f1:        float
    lr_auc_roc:   float
    is_active:    bool
    trained_at:   datetime

    model_config = {"from_attributes": True}


class TrainJobResponse(BaseModel):
    job_id:  str
    message: str


class TrainJobStatus(BaseModel):
    job_id:   str
    state:    str
    progress: int
    step:     Optional[str]
    label:    Optional[str]
    result:   Optional[dict]
    error:    Optional[str]
