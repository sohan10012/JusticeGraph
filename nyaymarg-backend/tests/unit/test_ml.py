"""
tests/unit/test_ml.py — Unit tests for ML models and prediction service.
"""
import pytest
from app.data.seed import get_registry


def test_rf_model_loaded():
    assert get_registry().rf_model is not None


def test_lr_model_loaded():
    assert get_registry().lr_model is not None


def test_vectorizer_loaded():
    assert get_registry().vectorizer is not None


def test_rf_model_predicts():
    import pandas as pd
    from app.ml.trainer import RF_FEATURES
    registry = get_registry()
    X = pd.DataFrame([registry.df_courts[RF_FEATURES].iloc[0]])
    prob = registry.rf_model.predict_proba(X)[0]
    assert abs(prob[0] + prob[1] - 1.0) < 1e-6
    assert 0 <= prob[1] <= 1


def test_lr_model_predicts():
    registry = get_registry()
    clean    = "property dispute inheritance legal heirs civil court"
    vec      = registry.vectorizer.transform([clean])
    prob     = registry.lr_model.predict_proba(vec)[0]
    assert abs(prob[0] + prob[1] - 1.0) < 1e-6


@pytest.mark.asyncio
async def test_prediction_service_outcome():
    from app.schemas.prediction import PredictionRequest
    from app.services.prediction_service import PredictionService

    svc    = PredictionService()
    req    = PredictionRequest(
        case_type="Civil",
        court_level="High Court",
        hearing_count=8,
        duration_days=365,
        judgment_text="property dispute regarding inheritance rights of legal heirs",
        keywords=["property", "inheritance"],
    )
    result = await svc.predict_case_outcome(req, user_id=None, db=None)
    assert result.predicted_outcome in ("Allowed", "Dismissed")
    assert 0.0 <= result.ensemble_confidence <= 1.0
    assert 0.0 <= result.rfc_confidence <= 1.0
    assert 0.0 <= result.logreg_confidence <= 1.0


def test_court_risk_service():
    from app.schemas.court import CourtRiskRequest
    from app.services.court_service import CourtService

    svc = CourtService()
    req = CourtRiskRequest(
        judge_strength=15,
        pending_cases=12000,
        monthly_filing_rate=400,
        monthly_disposal_rate=280,
        avg_disposal_time_days=540,
        infrastructure_score=6.2,
        digitization_level=0.55,
    )
    result = svc.predict_risk(req)
    assert result.risk_label in ("Low Risk", "Moderate Risk", "High Risk")
    assert 0.0 <= result.risk_probability <= 1.0
    assert len(result.contributing_factors) == 7


def test_clean_text():
    from app.ml.pipeline import clean_text
    assert clean_text("The murder case IPC 302!") == "murder case ipc"
    assert clean_text("") == ""
    assert clean_text(None) == ""  # type: ignore[arg-type]
