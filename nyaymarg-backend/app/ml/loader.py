"""
app/ml/loader.py — Load artefacts from disk or trigger fresh training.
"""
from __future__ import annotations

from pathlib import Path

import joblib
import structlog

from app.config import settings
from app.data.seed import get_registry

logger = structlog.get_logger(__name__)

ARTEFACT_DIR = Path(settings.MODEL_ARTEFACTS_DIR)


async def load_or_train_models() -> None:
    """
    Called once on startup (after initialise_seed_data).
    Loads rf_model, lr_model, vectorizer from disk if ALL three artefacts exist,
    otherwise trains fresh and saves them.
    """
    from app.ml.trainer import train_all_models  # local import avoids circular

    rf_path  = ARTEFACT_DIR / "rf_model.joblib"
    lr_path  = ARTEFACT_DIR / "lr_model.joblib"
    vec_path = ARTEFACT_DIR / "vectorizer.joblib"

    registry = get_registry()

    if rf_path.exists() and lr_path.exists() and vec_path.exists():
        logger.info("models.loading_from_disk")
        registry.rf_model   = joblib.load(rf_path)
        registry.lr_model   = joblib.load(lr_path)
        registry.vectorizer = joblib.load(vec_path)
        logger.info("models.loaded")
    else:
        logger.info("models.training_fresh")
        metrics = await train_all_models()
        logger.info("models.trained", metrics=metrics)


def get_model_registry():
    """Convenience alias used by health check."""
    return get_registry()
