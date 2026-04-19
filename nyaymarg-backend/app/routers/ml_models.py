"""
app/routers/ml_models.py — ML model management (Admin/Researcher only).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import UserRole, get_current_user, require_role
from app.database import get_db
from app.data.seed import get_registry
from app.schemas.notification import TrainJobResponse, TrainJobStatus

router = APIRouter()


@router.get("/active")
async def active_model(
    current: dict = Depends(get_current_user),
):
    registry = get_registry()
    return {
        "rf_model_loaded":   registry.rf_model is not None,
        "lr_model_loaded":   registry.lr_model is not None,
        "vectorizer_loaded": registry.vectorizer is not None,
        "metrics":           registry.model_metrics,
        "trained_at":        registry.model_trained_at.isoformat() if registry.model_trained_at else None,
    }


@router.post("/train", response_model=TrainJobResponse,
             dependencies=[require_role(UserRole.admin, UserRole.researcher)])
async def trigger_training(
    current: dict = Depends(get_current_user),
):
    """Trigger model retraining as a background Celery task."""
    try:
        from app.tasks.training_tasks import train_models_task
        task = train_models_task.delay(triggered_by=current.get("email", "unknown"))
        return TrainJobResponse(job_id=task.id, message="Training job queued")
    except Exception:
        # Celery not running — run synchronously
        from app.ml.trainer import train_all_models
        import asyncio
        metrics = await train_all_models()
        return TrainJobResponse(job_id="sync", message="Trained synchronously (Celery unavailable)")


@router.get("/train/{job_id}", response_model=TrainJobStatus,
            dependencies=[require_role(UserRole.admin, UserRole.researcher)])
async def training_job_status(job_id: str):
    """Poll Celery task status."""
    if job_id == "sync":
        return TrainJobStatus(job_id="sync", state="SUCCESS", progress=100,
                              step=None, label=None, result=None, error=None)
    try:
        from app.tasks.celery_app import celery_app
        task = celery_app.AsyncResult(job_id)
        info = task.info or {}
        return TrainJobStatus(
            job_id=job_id,
            state=str(task.state),
            progress=info.get("progress", 0),
            step=info.get("step"),
            label=info.get("label"),
            result=info if task.state == "SUCCESS" else None,
            error=str(info) if task.state == "FAILURE" else None,
        )
    except Exception as e:
        return TrainJobStatus(job_id=job_id, state="UNKNOWN", progress=0,
                              step=None, label=None, result=None, error=str(e))


@router.get("/feature-importance",
            dependencies=[require_role(UserRole.admin, UserRole.researcher)])
async def feature_importance():
    from app.ml.trainer import RF_FEATURES
    registry = get_registry()
    if registry.rf_model is None:
        return {"error": "Model not loaded"}
    return [
        {"feature": f, "importance": round(float(imp), 4)}
        for f, imp in sorted(
            zip(RF_FEATURES, registry.rf_model.feature_importances_),
            key=lambda x: x[1], reverse=True
        )
    ]


@router.get("/compare",
            dependencies=[require_role(UserRole.admin, UserRole.researcher)])
async def compare_models():
    registry = get_registry()
    return {
        "current": registry.model_metrics,
        "message": "Historical model versions require DB persistence — use /api/v1/model/history",
    }
