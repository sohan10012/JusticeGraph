"""
app/data/ddl_loader.py
=======================
DDL Judicial Dataset loader — replaces synthetic df_cases with real data.

The Development Data Lab dataset contains 81.2 million court cases
from India's lower judiciary (2010–2018), released under Open Database License.

Usage:
  1. Download state CSV files from https://www.devdatalab.org/judicial-data
  2. Place files in settings.DDL_LOCAL_PATH (default: ./data/ddl_judicial/)
  3. Set DDL_ENABLED=True in .env
  4. Restart the server — df_cases will be loaded from real data

The loader maps DDL columns to NyayMarg's internal schema and retrains
ML models automatically when real data is loaded.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import structlog

from app.config import settings
from app.data.seed import get_registry

logger = structlog.get_logger(__name__)

# ── DDL column → NyayMarg internal column mapping ─────────────────────────────
DDL_COLUMN_MAP: dict[str, str] = {
    "state":           "state",
    "dist_code":       "district_code",
    "court_no":        "court_id",
    "year":            "filing_year",
    "date_of_filing":  "filing_date",
    "date_of_decision":"decision_date",
    "type_name":       "case_type",
    "purpose_name":    "status",
    "disp_name":       "disposition",
    "pet_name":        "petitioner",
    "resp_name":       "respondent",
    "act":             "law_act",
    "section":         "law_section",
    "judge_position":  "judge_type",
}

# DDL case types → NyayMarg CASE_TYPES normalisation
_TYPE_MAP: dict[str, str] = {
    "civil":     "Civil",
    "criminal":  "Criminal",
    "family":    "Family",
    "labour":    "Labor",
    "revenue":   "Tax",
    "consumer":  "Civil",
}


async def load_ddl_dataset() -> bool:
    """
    Load DDL CSV/Parquet files and populate DataRegistry.df_cases.
    Returns True if data was loaded, False if skipped (files not found).

    Called on startup when DDL_ENABLED=True.
    """
    ddl_path = Path(settings.DDL_LOCAL_PATH)
    if not ddl_path.exists():
        logger.warning("ddl.path_not_found", path=str(ddl_path))
        return False

    # Accept both CSV and Parquet
    csv_files     = list(ddl_path.glob("*.csv"))
    parquet_files = list(ddl_path.glob("*.parquet"))
    all_files     = csv_files + parquet_files

    if not all_files:
        logger.warning("ddl.no_files_found", path=str(ddl_path))
        return False

    logger.info("ddl.loading", file_count=len(all_files))
    dfs: list[pd.DataFrame] = []

    for f in all_files:
        try:
            available_cols = list(DDL_COLUMN_MAP.keys())
            if f.suffix == ".parquet":
                df = pd.read_parquet(f, columns=_safe_cols(f, available_cols))
            else:
                df = pd.read_csv(
                    f,
                    usecols=lambda c: c in available_cols,
                    low_memory=False,
                )
            df = df.rename(columns=DDL_COLUMN_MAP)
            dfs.append(df)
        except Exception as exc:
            logger.warning("ddl.file_load_error", file=str(f), error=str(exc))
            continue

    if not dfs:
        return False

    df_real = pd.concat(dfs, ignore_index=True)

    # ── Derive required columns for NyayMarg schema ───────────────────────────
    # Binary outcome: decided=1, pending/dismissed=0
    df_real["outcome"] = df_real.get(
        "decision_date",
        pd.Series([None] * len(df_real)),
    ).notna().astype(int)

    # Normalise case_type
    df_real["case_type"] = (
        df_real["case_type"]
        .fillna("Civil")
        .str.lower()
        .map(lambda t: _TYPE_MAP.get(t, "Civil"))
    )

    # Derive clean_text for NLP pipeline (combine act + section)
    import re

    def _make_clean(row: pd.Series) -> str:
        parts = [
            str(row.get("law_act", "") or ""),
            str(row.get("law_section", "") or ""),
            str(row.get("case_type", "") or "").lower(),
            str(row.get("state", "") or "").lower(),
        ]
        raw   = " ".join(parts)
        clean = re.sub(r"[^a-z\s]", "", raw.lower())
        return re.sub(r"\s+", " ", clean).strip()

    df_real["clean_text"] = df_real.apply(_make_clean, axis=1)
    df_real["case_id"]    = [f"DDL_{i:08d}" for i in range(len(df_real))]
    df_real["case_title"] = (
        df_real["petitioner"].fillna("Unknown")
        + " vs "
        + df_real["respondent"].fillna("Unknown")
    )
    df_real["hearing_count"]    = 0    # DDL doesn't contain hearing history
    df_real["complexity_score"] = 5.0
    df_real["days_pending"]     = (
        pd.to_datetime(df_real.get("decision_date"), errors="coerce")
        - pd.to_datetime(df_real.get("filing_date"),  errors="coerce")
    ).dt.days.fillna(0).astype(int)

    # Sample to SEED_CASES if the dataset is too large for in-memory ML
    n = min(len(df_real), settings.SEED_CASES * 10)  # cap at 70,000 for dev
    if len(df_real) > n:
        df_real = df_real.sample(n=n, random_state=settings.RANDOM_SEED).reset_index(drop=True)

    registry          = get_registry()
    registry.df_cases = df_real

    logger.info(
        "ddl.loaded",
        rows=len(df_real),
        outcome_balance=float(df_real["outcome"].mean()),
    )
    return True


def _safe_cols(path: Path, wanted: list[str]) -> list[str]:
    """Return intersection of wanted columns and columns in file."""
    try:
        import pyarrow.parquet as pq  # type: ignore
        existing = pq.read_schema(str(path)).names
        return [c for c in wanted if c in existing]
    except Exception:
        return wanted
