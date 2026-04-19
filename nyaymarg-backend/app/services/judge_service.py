"""
app/services/judge_service.py — Judge data access layer.
"""
from __future__ import annotations

from app.data.seed import get_registry


class JudgeService:

    def list_judges(
        self,
        state:          str | None = None,
        specialization: str | None = None,
        page:           int = 1,
        page_size:      int = 20,
    ) -> tuple[list[dict], int]:
        df = get_registry().df_judges.copy()
        if state:
            df = df[df["state"].str.lower() == state.lower()]
        if specialization:
            df = df[df["specialization"].str.lower() == specialization.lower()]
        total = len(df)
        start = (page - 1) * page_size
        return df.iloc[start : start + page_size].to_dict(orient="records"), total

    def get_judge(self, judge_id: str) -> dict | None:
        df  = get_registry().df_judges
        row = df[df["judge_id"] == judge_id]
        return None if row.empty else row.iloc[0].to_dict()

    def leaderboard(self, top_n: int = 20) -> list[dict]:
        df = get_registry().df_judges.nlargest(top_n, "rating_score").copy()
        df = df.reset_index(drop=True)
        records = df.to_dict(orient="records")
        for i, r in enumerate(records):
            r["rank"] = i + 1
        return records

    def bias_analysis(self) -> dict:
        df = get_registry().df_judges
        return {
            "mean":   round(float(df["bias_index"].mean()), 4),
            "median": round(float(df["bias_index"].median()), 4),
            "min":    round(float(df["bias_index"].min()), 4),
            "max":    round(float(df["bias_index"].max()), 4),
            "high_bias_count": int((df["bias_index"] > 0.7).sum()),
        }

    def performance_stats(self) -> dict:
        df = get_registry().df_judges
        return {
            "avg_reversal_rate":          round(float(df["reversal_rate"].mean()), 4),
            "avg_judgment_time_days":     round(float(df["avg_judgment_time_days"].mean()), 1),
            "top_reversal_rate":          round(float(df["reversal_rate"].max()), 4),
            "lowest_avg_judgment_days":   round(float(df["avg_judgment_time_days"].min()), 1),
        }

    def get_cases_for_judge(
        self, judge_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[dict], int]:
        df    = get_registry().df_cases
        df    = df[df["judge_id"] == judge_id]
        total = len(df)
        start = (page - 1) * page_size
        return df.iloc[start : start + page_size].to_dict(orient="records"), total
