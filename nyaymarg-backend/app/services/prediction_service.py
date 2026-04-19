"""
app/services/prediction_service.py
===================================
Core prediction logic — ensemble of RFC (court risk) + LogReg (case outcome).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pandas as pd

from app.config import settings
from app.data.seed import get_registry
from app.ml.pipeline import clean_text
from app.ml.trainer import RF_FEATURES
from app.schemas.prediction import PredictionRequest, PredictionResponse


# ── Case-type → numeric encoding ─────────────────────────────────────────────
_CASE_TYPE_CODES: dict[str, int] = {
    "Criminal": 0, "Civil": 1, "Constitutional": 2, "Corporate": 3,
    "Family":   4, "Property": 5, "Tax": 6, "Cybercrime": 7,
    "Environmental": 8, "Labor": 9,
}

_COURT_LEVEL_CODES: dict[str, int] = {
    "District Court": 0, "Sessions Court": 1,
    "High Court":     2, "Supreme Court":  3,
}


class PredictionService:

    async def predict_case_outcome(
        self,
        request: PredictionRequest,
        user_id: uuid.UUID | None,
        db=None,           # AsyncSession — optional (None in unit tests)
    ) -> PredictionResponse:
        from app.core.exceptions import ModelNotReadyError

        registry = get_registry()
        if registry.lr_model is None or registry.rf_model is None:
            raise ModelNotReadyError()

        # ── 1. NLP pathway (LogReg) ───────────────────────────────────────────
        cleaned   = clean_text(request.judgment_text)
        vec       = registry.vectorizer.transform([cleaned])
        lr_prob   = float(registry.lr_model.predict_proba(vec)[0][1])

        # ── 2. Structured pathway (RFC) ───────────────────────────────────────
        rf_features = self._build_rf_features(request)
        X           = pd.DataFrame([rf_features], columns=RF_FEATURES)
        rf_prob     = float(registry.rf_model.predict_proba(X)[0][1])

        # ── 3. Weighted ensemble ──────────────────────────────────────────────
        ensemble = settings.RFC_WEIGHT * rf_prob + settings.LR_WEIGHT * lr_prob
        outcome  = "Allowed" if ensemble >= 0.5 else "Dismissed"

        # ── 4. Feature importances ────────────────────────────────────────────
        importances  = registry.rf_model.feature_importances_
        top_features = [
            {"feature": f, "importance": round(float(imp), 4)}
            for f, imp in sorted(
                zip(RF_FEATURES, importances), key=lambda x: x[1], reverse=True
            )[:5]
        ]

        # ── 5. Persist to DB (if session provided) ────────────────────────────
        pred_id    = uuid.uuid4()
        created_at = datetime.now(timezone.utc)
        if db is not None:
            from app.models.prediction import Prediction
            pred = Prediction(
                id=pred_id,
                user_id=user_id,
                case_type=request.case_type,
                court_level=request.court_level,
                hearing_count=request.hearing_count,
                duration_days=request.duration_days,
                judgment_text=request.judgment_text,
                predicted_outcome=outcome,
                rfc_confidence=round(rf_prob, 4),
                logreg_confidence=round(lr_prob, 4),
                ensemble_confidence=round(ensemble, 4),
                top_features=top_features,
                input_snapshot=request.model_dump(),
                created_at=created_at,
            )
            db.add(pred)
            await db.flush()

        # ── 6. Count similar cases (quick estimate) ───────────────────────────
        similar_count = min(int(len(registry.df_cases) * 0.01), 5)

        return PredictionResponse(
            prediction_id=pred_id,
            predicted_outcome=outcome,
            rfc_confidence=round(rf_prob, 4),
            logreg_confidence=round(lr_prob, 4),
            ensemble_confidence=round(ensemble, 4),
            top_features=top_features,
            similar_cases_count=similar_count,
            analyzed_at=created_at,
        )

    # ── Batch ─────────────────────────────────────────────────────────────────
    async def predict_batch(
        self,
        requests: list[PredictionRequest],
        user_id:  uuid.UUID | None,
        db=None,
    ) -> list[PredictionResponse]:
        results = []
        for req in requests:
            results.append(await self.predict_case_outcome(req, user_id, db))
        return results

    # ── Helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _build_rf_features(request: PredictionRequest) -> list[float]:
        """
        Map PredictionRequest fields to the 7 RF training features.
        Uses median court values from DataRegistry for context.
        """
        registry = get_registry()
        df       = registry.df_courts

        # Use aggregate stats as proxy features
        judge_strength        = float(df["judge_strength"].median())
        pending_cases         = float(df["pending_cases"].median())
        monthly_filing_rate   = float(df["monthly_filing_rate"].median())
        monthly_disposal_rate = float(df["monthly_disposal_rate"].median())

        return [
            judge_strength,
            pending_cases,
            monthly_filing_rate,
            monthly_disposal_rate,
            float(request.duration_days),
            5.0,   # default infrastructure_score
            0.5,   # default digitization_level
        ]
