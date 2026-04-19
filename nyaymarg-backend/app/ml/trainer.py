"""
app/ml/trainer.py
=================
Trains both ML models from the DataRegistry synthetic corpus:
  - Model 1: RandomForestClassifier — court backlog risk (binary)
  - Model 2: LogisticRegression + TfidfVectorizer — case outcome (binary)

All hyperparameters mirror the JusticeGraph spec.
Artefacts are persisted via joblib to MODEL_ARTEFACTS_DIR.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import cross_val_score, train_test_split

from app.config import settings
from app.data.seed import get_registry

ARTEFACT_DIR = Path(settings.MODEL_ARTEFACTS_DIR)

RF_FEATURES: list[str] = [
    "judge_strength",
    "pending_cases",
    "monthly_filing_rate",
    "monthly_disposal_rate",
    "avg_disposal_time_days",
    "infrastructure_score",
    "digitization_level",
]


async def train_all_models() -> dict:
    """
    Public async entry point — runs training in a thread executor to avoid
    blocking the event loop.
    Returns evaluation metrics dict.
    """
    loop = asyncio.get_event_loop()
    registry = get_registry()
    metrics = await loop.run_in_executor(None, _train_sync, registry)
    registry.model_metrics   = metrics
    registry.model_trained_at = datetime.now(timezone.utc)
    return metrics


def _train_sync(registry) -> dict:
    """Blocking training routine — called inside executor."""
    ARTEFACT_DIR.mkdir(parents=True, exist_ok=True)
    
    import warnings
    warnings.filterwarnings("ignore")

    # ── Model 1: Court Backlog Risk (RandomForest) ───────────────────────────
    X_rf = registry.df_courts[RF_FEATURES]
    y_rf = (registry.df_courts["backlog_risk_score"] > 0.6).astype(int)

    X_rf_train, X_rf_test, y_rf_train, y_rf_test = train_test_split(
        X_rf, y_rf, test_size=0.25, random_state=42
    )

    rf = RandomForestClassifier(
        n_estimators=settings.DEFAULT_N_ESTIMATORS,
        max_depth=10,
        random_state=42,
        class_weight="balanced",
    )
    rf.fit(X_rf_train, y_rf_train)

    rf_cv  = float(cross_val_score(rf, X_rf, y_rf, cv=5, scoring="f1").mean())
    rf_acc = float(accuracy_score(y_rf_test, rf.predict(X_rf_test)))

    # ── Model 2: Case Outcome (LogisticRegression + TF-IDF) ─────────────────
    from app.ml.pipeline import clean_text  # noqa: PLC0415

    corpus  = registry.df_cases["clean_text"].fillna("").tolist()
    labels  = registry.df_cases["outcome"].astype(int).tolist()

    X_lr_train, X_lr_test, y_lr_train, y_lr_test = train_test_split(
        corpus, labels, test_size=0.2, random_state=42
    )

    vec = TfidfVectorizer(max_features=500, ngram_range=(1, 2))
    X_train_vec = vec.fit_transform(X_lr_train)
    X_test_vec  = vec.transform(X_lr_test)

    lr = LogisticRegression(max_iter=500, random_state=42, C=1.0)
    lr.fit(X_train_vec, y_lr_train)

    y_pred    = lr.predict(X_test_vec)
    y_proba   = lr.predict_proba(X_test_vec)[:, 1]
    lr_acc    = float(accuracy_score(y_lr_test, y_pred))
    lr_f1     = float(f1_score(y_lr_test, y_pred))
    lr_auc    = float(roc_auc_score(y_lr_test, y_proba))

    # ── Persist artefacts ────────────────────────────────────────────────────
    joblib.dump(rf,  ARTEFACT_DIR / "rf_model.joblib")
    joblib.dump(lr,  ARTEFACT_DIR / "lr_model.joblib")
    joblib.dump(vec, ARTEFACT_DIR / "vectorizer.joblib")

    # ── Update in-memory registry ────────────────────────────────────────────
    registry.rf_model   = rf
    registry.lr_model   = lr
    registry.vectorizer = vec

    return {
        "rf_model": {
            "accuracy": round(rf_acc, 4),
            "cv_f1":    round(rf_cv, 4),
            "features": RF_FEATURES,
        },
        "lr_model": {
            "accuracy": round(lr_acc, 4),
            "f1":       round(lr_f1, 4),
            "auc_roc":  round(lr_auc, 4),
        },
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
