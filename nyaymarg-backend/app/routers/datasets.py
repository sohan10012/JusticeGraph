"""
app/routers/datasets.py — Dataset upload and management endpoints.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import UserRole, get_current_user, require_role
from app.database import get_db
from app.models.dataset import Dataset
from app.schemas.notification import DatasetOut, DatasetStatusResponse

router = APIRouter()
_UPLOAD_DIR = Path(settings.UPLOAD_DIR)


@router.post("/upload", response_model=DatasetOut, status_code=201)
async def upload_dataset(
    file:    UploadFile = File(...),
    current: dict = Depends(get_current_user),
    db:      AsyncSession = Depends(get_db),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Only {settings.ALLOWED_EXTENSIONS} files are allowed")

    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ds_id    = uuid.uuid4()
    filename = f"{ds_id}{ext}"
    dest     = _UPLOAD_DIR / filename

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, "File exceeds maximum size")

    dest.write_bytes(content)

    ds = Dataset(
        id=ds_id,
        user_id=current["id"],
        name=file.filename or filename,
        filename=filename,
        file_path=str(dest),
        file_size=len(content),
        status="pending",
    )
    db.add(ds)
    await db.flush()

    # Trigger background Celery task
    try:
        from app.tasks.ingestion_tasks import process_dataset_task
        process_dataset_task.delay(str(ds_id), str(dest))
    except Exception:
        pass  # Celery unavailable in dev — dataset remains in 'pending'

    return DatasetOut.model_validate(ds)


@router.get("/", response_model=list[DatasetOut])
async def list_datasets(
    current: dict = Depends(get_current_user),
    db:      AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Dataset).where(Dataset.user_id == current["id"]).order_by(Dataset.created_at.desc())
    )
    return [DatasetOut.model_validate(d) for d in result.scalars().all()]


@router.get("/{dataset_id}", response_model=DatasetOut)
async def get_dataset(
    dataset_id: UUID,
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current["id"])
    )
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(404, "Dataset not found")
    return DatasetOut.model_validate(ds)


@router.get("/{dataset_id}/status", response_model=DatasetStatusResponse)
async def dataset_status(
    dataset_id: UUID,
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current["id"])
    )
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(404, "Dataset not found")
    return DatasetStatusResponse(id=ds.id, status=str(ds.status), error=ds.error_msg)


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: UUID,
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import delete
    result = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == current["id"])
    )
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(404, "Dataset not found")
    # Delete file
    try:
        Path(str(ds.file_path)).unlink(missing_ok=True)
    except Exception:
        pass
    await db.execute(delete(Dataset).where(Dataset.id == dataset_id))
