"""
app/ml/evaluator.py — Cross-validation and evaluation utilities.
"""
from __future__ import annotations

from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import cross_val_score


def evaluate_classifier(model, X_test, y_test) -> dict:
    """Return accuracy, F1, and AUC-ROC for a fitted classifier."""
    y_pred  = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    return {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "f1":       round(float(f1_score(y_test, y_pred)), 4),
        "auc_roc":  round(float(roc_auc_score(y_test, y_proba)), 4),
    }


def cross_validate_f1(model, X, y, cv: int = 5) -> float:
    return round(float(cross_val_score(model, X, y, cv=cv, scoring="f1").mean()), 4)
