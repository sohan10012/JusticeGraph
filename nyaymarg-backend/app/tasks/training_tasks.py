"""
app/tasks/training_tasks.py — ML model retraining background task.
"""
from __future__ import annotations

import asyncio

from app.tasks.celery_app import celery_app

_STEPS = [
    ("loading",       "Loading dataset from registry..."),
    ("preprocessing", "Running NLP pipeline..."),
    ("training_rfc",  "Training Random Forest Classifier..."),
    ("training_lr",   "Training Logistic Regression..."),
    ("cross_val",     "Running 5-fold cross-validation..."),
    ("evaluating",    "Computing accuracy, F1, AUC-ROC..."),
    ("saving",        "Serialising model artefacts..."),
]


@celery_app.task(bind=True, max_retries=3, name="tasks.train_models")
def train_models_task(self, triggered_by: str = "api"):
    """
    Retrain both ML models in the background.
    Provides real progress updates via Celery state.
    """
    n = len(_STEPS)
    for i, (step_key, step_label) in enumerate(_STEPS):
        self.update_state(
            state="PROGRESS",
            meta={
                "step":     step_key,
                "label":    step_label,
                "progress": int((i / n) * 100),
            },
        )

    # Actual training (synchronous in worker context)
    from app.data.seed import get_registry, initialise_seed_data
    from app.ml.trainer import _train_sync

    # Re-use existing registry (worker shares memory)
    registry = get_registry()
    if registry.df_courts is None:
        asyncio.run(initialise_seed_data())

    result = _train_sync(registry)

    self.update_state(state="PROGRESS", meta={"step": "done", "label": "Complete", "progress": 100})
    return {"status": "complete", "metrics": result, "triggered_by": triggered_by}
