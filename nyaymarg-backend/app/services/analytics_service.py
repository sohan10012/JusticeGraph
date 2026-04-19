"""
app/services/analytics_service.py
===================================
Chart and stats generation. All existing chart logic from JusticeGraph is
migrated here. Supports JSON data or base64-encoded PNG (matplotlib dark theme).
"""
from __future__ import annotations

import base64
import io
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from app.data.seed import get_registry

# ── NyayMarg chart theme ─────────────────────────────────────────────────────
NAVY    = "#0D1B2A"
TEAL    = "#0F3D3E"
GOLD    = "#C9993F"
DANGER  = "#B5341D"
MUTED   = "#8C9BAB"
LIGHT   = "#F8F9FA"

_STYLE = {
    "figure.facecolor":  NAVY,
    "axes.facecolor":    "#162840",
    "axes.edgecolor":    "#1B3A5C",
    "text.color":        LIGHT,
    "axes.labelcolor":   LIGHT,
    "xtick.color":       MUTED,
    "ytick.color":       MUTED,
    "grid.color":        "#1B3A5C",
    "grid.linewidth":    0.5,
    "axes.titlecolor":   LIGHT,
}


def _apply_style() -> None:
    plt.rcParams.update(_STYLE)


def _fig_to_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.read()).decode()


class AnalyticsService:

    def overview(self) -> dict:
        registry = get_registry()
        df_c = registry.df_courts
        df_j = registry.df_judges
        df_k = registry.df_cases

        pending = int((df_k["status"] == "Pending").sum())
        decided = int((df_k["status"] == "Decided").sum())

        return {
            "total_courts":     int(len(df_c)),
            "total_judges":     int(len(df_j)),
            "total_cases":      int(len(df_k)),
            "pending_cases":    pending,
            "decided_cases":    decided,
            "high_risk_courts": int((df_c["risk_category"].astype(str) == "High Risk").sum()),
            "avg_pending_days": round(float(df_k["days_pending"].mean()), 1),
            "prediction_count": 0,  # populated from DB in real deployment
        }

    def outcomes(self, fmt: str = "json") -> dict | str:
        df = get_registry().df_cases
        dist = df["status"].value_counts().to_dict()
        if fmt == "json":
            return dist
        # PNG
        _apply_style()
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(dist.keys(), dist.values(), color=GOLD)
        ax.set_title("Case Outcome Distribution", pad=12)
        ax.set_xlabel("Status")
        ax.set_ylabel("Count")
        return _fig_to_b64(fig)

    def court_level_chart(self, fmt: str = "json") -> dict | str:
        df = get_registry().df_cases
        ct = df.groupby(
            df["court_id"].map(
                get_registry().df_courts.set_index("court_id")["court_type"]
            )
        )["status"].count().to_dict()
        if fmt == "json":
            return ct
        _apply_style()
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(ct.keys(), ct.values(), color=GOLD)
        ax.set_title("Cases by Court Type", pad=12)
        return _fig_to_b64(fig)

    def duration_trend(self, fmt: str = "json") -> dict | str:
        df = get_registry().df_cases
        bins = [0, 180, 365, 1095, 1825, float("inf")]
        labels = ["<6m", "6m-1y", "1-3y", "3-5y", "5y+"]
        df = df.copy()
        df["bucket"] = pd.cut(df["days_pending"], bins=bins, labels=labels)
        dist = df["bucket"].value_counts().sort_index().to_dict()
        if fmt == "json":
            return {str(k): int(v) for k, v in dist.items()}
        _apply_style()
        keys   = [str(k) for k in dist.keys()]
        values = list(dist.values())
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(keys, values, marker="o", color=GOLD, linewidth=2)
        ax.fill_between(keys, values, alpha=0.25, color=GOLD)
        ax.set_title("Case Pendency Distribution", pad=12)
        return _fig_to_b64(fig)

    def case_types(self, fmt: str = "json") -> dict | str:
        df   = get_registry().df_cases
        dist = df["case_type"].value_counts().to_dict()
        if fmt == "json":
            return dist
        _apply_style()
        fig, ax = plt.subplots(figsize=(7, 4))
        colors = [GOLD, TEAL, DANGER, "#4A90D9", "#7BC67E",
                  "#FF9F40", "#C77DFF", "#FF6B6B", "#6BCBF5", "#FFD166"]
        ax.pie(dist.values(), labels=dist.keys(), autopct="%1.1f%%",
               colors=colors[:len(dist)], textprops={"color": LIGHT})
        ax.set_title("Case Type Distribution", pad=12)
        return _fig_to_b64(fig)

    def judge_performance(self, fmt: str = "json") -> dict | str:
        df = get_registry().df_judges
        stats = {
            "avg_rating_score":          round(float(df["rating_score"].mean()), 2),
            "avg_reversal_rate":         round(float(df["reversal_rate"].mean()), 4),
            "avg_judgment_time_days":    round(float(df["avg_judgment_time_days"].mean()), 1),
            "rating_distribution":       df["rating_score"].describe().round(2).to_dict(),
        }
        if fmt == "json":
            return stats
        _apply_style()
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist(df["rating_score"], bins=15, color=GOLD, edgecolor=NAVY)
        ax.set_title("Judge Rating Score Distribution", pad=12)
        ax.set_xlabel("Rating Score")
        return _fig_to_b64(fig)

    def state_heatmap(self, fmt: str = "json") -> dict | str:
        df_cases  = get_registry().df_cases
        df_courts = get_registry().df_courts
        state_cases = df_cases["state"].value_counts().to_dict()
        state_risk  = (
            df_courts[df_courts["risk_category"].astype(str) == "High Risk"]["state"]
            .value_counts().to_dict()
        )
        states = sorted(state_cases.keys())
        result = [
            {
                "state":       s,
                "case_count":  state_cases.get(s, 0),
                "high_risk_courts": state_risk.get(s, 0),
            }
            for s in states
        ]
        if fmt == "json":
            return result
        return result  # map visualisation is handled by the frontend

    def model_performance(self) -> dict:
        r = get_registry()
        if not r.model_metrics:
            return {"status": "models not yet evaluated"}
        return {
            **r.model_metrics,
            "trained_at": r.model_trained_at.isoformat() if r.model_trained_at else None,
        }


# Delayed import to avoid circular at module load
import pandas as pd  # noqa: E402
