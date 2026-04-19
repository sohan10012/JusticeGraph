"""
app/services/court_service.py — Court data access layer (in-memory DataRegistry).
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from app.data.seed import get_registry
from app.schemas.court import CourtOut, CourtRiskRequest, CourtRiskResponse, CourtSummary


class CourtService:

    # ── List / filter ─────────────────────────────────────────────────────────
    def list_courts(
        self,
        state:      str | None = None,
        court_type: str | None = None,
        risk:       str | None = None,
        page:       int = 1,
        page_size:  int = 20,
    ) -> tuple[list[dict], int]:
        df = get_registry().df_courts.copy()
        if state:
            df = df[df["state"].str.lower() == state.lower()]
        if court_type:
            df = df[df["court_type"].str.lower() == court_type.lower()]
        if risk:
            df = df[df["risk_category"].astype(str).str.lower() == risk.lower()]

        total = len(df)
        start = (page - 1) * page_size
        chunk = df.iloc[start : start + page_size]
        return chunk.to_dict(orient="records"), total

    def get_court(self, court_id: str) -> dict | None:
        df = get_registry().df_courts
        row = df[df["court_id"] == court_id]
        if row.empty:
            return None
        return row.iloc[0].to_dict()

    def get_summary(self) -> dict:
        df = get_registry().df_courts
        by_risk = df["risk_category"].astype(str).value_counts().to_dict()
        by_state = df["state"].value_counts().to_dict()
        by_type  = df["court_type"].value_counts().to_dict()
        return {
            "total_courts":     int(len(df)),
            "by_risk_category": by_risk,
            "by_state":         by_state,
            "by_court_type":    by_type,
        }

    def get_risk_map(self) -> list[dict]:
        """Returns slim court records suitable for map visualisation."""
        df = get_registry().df_courts
        fields = ["court_id", "court_name", "city", "state", "court_type",
                  "backlog_risk_score", "risk_category", "pending_cases"]
        return df[fields].to_dict(orient="records")

    def get_judges_for_court(self, court_id: str) -> list[dict]:
        reg = get_registry()
        df  = reg.df_judges[reg.df_judges["court_id"] == court_id]
        return df.to_dict(orient="records")

    def get_cases_for_court(
        self, court_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[dict], int]:
        df    = get_registry().df_cases
        df    = df[df["court_id"] == court_id]
        total = len(df)
        start = (page - 1) * page_size
        chunk = df.iloc[start : start + page_size]
        return chunk.to_dict(orient="records"), total

    # ── RF risk prediction ────────────────────────────────────────────────────
    def predict_risk(self, req: CourtRiskRequest) -> CourtRiskResponse:
        from app.core.exceptions import ModelNotReadyError

        registry = get_registry()
        if registry.rf_model is None:
            raise ModelNotReadyError()

        import numpy as np
        from app.ml.trainer import RF_FEATURES

        feature_vec = [
            req.judge_strength,
            req.pending_cases,
            req.monthly_filing_rate,
            req.monthly_disposal_rate,
            req.avg_disposal_time_days,
            req.infrastructure_score,
            req.digitization_level,
        ]
        import pandas as pd
        X = pd.DataFrame([feature_vec], columns=RF_FEATURES)
        prob = float(registry.rf_model.predict_proba(X)[0][1])

        if prob > 0.6:
            label = "High Risk"
        elif prob > 0.3:
            label = "Moderate Risk"
        else:
            label = "Low Risk"

        # Feature importances
        importances = registry.rf_model.feature_importances_
        factors = [
            {"feature": f, "importance": round(float(imp), 4), "value": float(val)}
            for f, imp, val in sorted(
                zip(RF_FEATURES, importances, feature_vec),
                key=lambda x: x[1], reverse=True
            )
        ]

        scaler = registry.scaler
        raw_score = float(prob)

        return CourtRiskResponse(
            risk_label=label,
            risk_probability=round(prob, 4),
            risk_score=round(raw_score, 4),
            contributing_factors=factors,
        )
