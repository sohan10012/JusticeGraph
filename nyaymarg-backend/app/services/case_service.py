"""
app/services/case_service.py — Case data access layer.
"""
from __future__ import annotations

from app.data.seed import get_registry
from app.ml.pipeline import clean_text


class CaseService:

    def list_cases(
        self,
        case_type: str | None = None,
        status:    str | None = None,
        state:     str | None = None,
        court_id:  str | None = None,
        page:      int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        df = get_registry().df_cases.copy()
        if case_type:
            df = df[df["case_type"].str.lower() == case_type.lower()]
        if status:
            df = df[df["status"].str.lower() == status.lower()]
        if state:
            df = df[df["state"].str.lower() == state.lower()]
        if court_id:
            df = df[df["court_id"] == court_id]
        total = len(df)
        start = (page - 1) * page_size
        return df.iloc[start : start + page_size].to_dict(orient="records"), total

    def get_case(self, case_id: str) -> dict | None:
        df  = get_registry().df_cases
        row = df[df["case_id"] == case_id]
        return None if row.empty else row.iloc[0].to_dict()

    def search(self, query: str, page: int = 1, page_size: int = 20) -> tuple[list[dict], int]:
        """Simple substring search on case_title and clean_text."""
        df  = get_registry().df_cases
        q   = query.lower()
        mask = (
            df["case_title"].str.lower().str.contains(q, na=False)
            | df["clean_text"].str.lower().str.contains(q, na=False)
        )
        filtered = df[mask]
        total    = len(filtered)
        start    = (page - 1) * page_size
        chunk    = filtered.iloc[start : start + page_size].copy()
        chunk["score"] = 1.0
        return chunk.to_dict(orient="records"), total

    def get_summary(self) -> dict:
        df = get_registry().df_cases
        return {
            "total":           int(len(df)),
            "by_status":       df["status"].value_counts().to_dict(),
            "by_type":         df["case_type"].value_counts().to_dict(),
            "by_state":        df["state"].value_counts().head(10).to_dict(),
        }

    def pendency_distribution(self) -> dict:
        df     = get_registry().df_cases
        counts = {
            "0-180 days":     int((df["days_pending"] < 180).sum()),
            "180-365 days":   int(((df["days_pending"] >= 180) & (df["days_pending"] < 365)).sum()),
            "1-3 years":      int(((df["days_pending"] >= 365) & (df["days_pending"] < 1095)).sum()),
            "3-5 years":      int(((df["days_pending"] >= 1095) & (df["days_pending"] < 1825)).sum()),
            "5+ years":       int((df["days_pending"] >= 1825).sum()),
        }
        return {"distribution": counts, "avg_days_pending": round(float(df["days_pending"].mean()), 1)}
