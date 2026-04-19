"""
app/data/seed.py
================
Synthetic dataset generation for NyayMarg.
Generates df_courts (120), df_judges (300), df_cases (7000), df_laws (9).
Called once on startup; data cached in-memory via DataRegistry singleton.

All generation logic is deterministic (np.random.seed = RANDOM_SEED).
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from app.config import settings

# ── State → City mapping (18 states) ─────────────────────────────────────────
STATE_CITY_MAP: dict[str, list[str]] = {
    "Delhi":          ["New Delhi", "South Delhi", "Rohini"],
    "Maharashtra":    ["Mumbai", "Pune", "Nagpur"],
    "Karnataka":      ["Bengaluru", "Mysuru", "Mangalore"],
    "Tamil Nadu":     ["Chennai", "Coimbatore", "Madurai"],
    "West Bengal":    ["Kolkata", "Siliguri"],
    "Telangana":      ["Hyderabad", "Warangal"],
    "Gujarat":        ["Ahmedabad", "Surat", "Vadodara"],
    "Rajasthan":      ["Jaipur", "Udaipur", "Jodhpur"],
    "Uttar Pradesh":  ["Lucknow", "Noida", "Kanpur"],
    "Punjab":         ["Chandigarh", "Amritsar", "Ludhiana"],
    "Kerala":         ["Kochi", "Thiruvananthapuram", "Kozhikode"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Gwalior"],
    "Bihar":          ["Patna", "Gaya"],
    "Odisha":         ["Bhubaneswar", "Cuttack"],
    "Haryana":        ["Gurgaon", "Faridabad"],
    "Assam":          ["Guwahati", "Dibrugarh"],
    "Chhattisgarh":   ["Raipur", "Bilaspur"],
    "Jharkhand":      ["Ranchi", "Jamshedpur"],
}

COURT_TYPES: list[str] = [
    "District Court", "High Court", "Sessions Court", "Supreme Court"
]
CASE_TYPES: list[str] = [
    "Criminal", "Civil", "Constitutional", "Corporate", "Family",
    "Property", "Tax", "Cybercrime", "Environmental", "Labor",
]
CASE_STATUSES: list[str] = [
    "Pending", "Decided", "Transferred", "Dismissed", "Adjourned"
]
SPECIALIZATIONS: list[str] = [
    "Criminal", "Civil", "Constitutional", "Corporate", "Family",
    "Property", "Tax", "Cybercrime", "Environmental",
]

# ── Laws seed (9 entries) ─────────────────────────────────────────────────────
LAWS_SEED: list[dict[str, Any]] = [
    {"law_id": "IPC_302", "law_name": "IPC Section 302",         "category": "Criminal",       "description": "Punishment for murder",                                          "severity": 10},
    {"law_id": "IPC_420", "law_name": "IPC Section 420",         "category": "Criminal",       "description": "Cheating and dishonestly inducing delivery of property",         "severity": 7},
    {"law_id": "CPC_9",   "law_name": "CPC Section 9",           "category": "Civil",          "description": "Courts to try all civil suits unless barred",                    "severity": 5},
    {"law_id": "IT_66",   "law_name": "IT Act Section 66",       "category": "Cybercrime",     "description": "Computer-related offences",                                      "severity": 8},
    {"law_id": "ART_21",  "law_name": "Article 21",              "category": "Constitutional", "description": "Protection of life and personal liberty",                        "severity": 10},
    {"law_id": "ART_14",  "law_name": "Article 14",              "category": "Constitutional", "description": "Equality before law",                                             "severity": 9},
    {"law_id": "GST_73",  "law_name": "GST Act Section 73",      "category": "Tax",            "description": "Determination of tax not paid or short paid",                    "severity": 6},
    {"law_id": "ENV_15",  "law_name": "Environment Act Section 15", "category": "Environmental","description": "Penalty for contravention of the provisions",                   "severity": 8},
    {"law_id": "LAB_25F", "law_name": "Industrial Disputes Act 25F","category": "Labor",       "description": "Conditions precedent to retrenchment of workmen",                "severity": 6},
]

# ── Case-text templates for NLP corpus ───────────────────────────────────────
_CASE_TEXT_TEMPLATES: list[str] = [
    "petitioner challenges the order {act} on grounds of violation fundamental rights",
    "respondent accused of {act} charges filed under relevant sections indian penal code",
    "appeal against conviction sentence lower court {act} case evidence examined",
    "writ petition filed high court challenging government decision {act} policy matter",
    "civil dispute regarding property rights inheritance {act} succession matter pending",
    "criminal complaint filed police station {act} investigation underway chargesheet filed",
    "corruption charges against public servant {act} disproportionate assets case vigilance",
    "consumer complaint regarding deficiency service {act} product liability damages sought",
    "labour dispute wrongful termination {act} reinstatement compensation claimed workers",
    "tax evasion case revenue department {act} assessment penalty proceedings initiated",
    "cybercrime case involving {act} digital evidence electronic records examined forensics",
    "environmental violation industrial unit {act} pollution control board action taken",
    "constitutional validity challenged {act} fundamental rights directive principles examined",
    "corporate fraud case promoters directors {act} shareholder rights minority interests",
    "family dispute maintenance alimony {act} custody child welfare paramount consideration",
]

_ACTS: list[str] = [
    "IPC 302 murder", "IPC 420 cheating", "CPC civil procedure",
    "IT Act cybercrime", "Article 21 liberty", "Article 14 equality",
    "GST evasion tax", "Environment Act pollution", "Industrial Disputes retrenchment",
    "Prevention Corruption Act", "Consumer Protection Act", "NDPS narcotics",
]

# ── DataRegistry singleton ────────────────────────────────────────────────────

class DataRegistry:
    """Single in-memory store for all generated DataFrames and trained ML objects."""

    df_courts:   pd.DataFrame | None = None
    df_judges:   pd.DataFrame | None = None
    df_cases:    pd.DataFrame | None = None
    df_laws:     pd.DataFrame | None = None

    rf_model     = None  # RandomForestClassifier
    lr_model     = None  # LogisticRegression
    vectorizer   = None  # TfidfVectorizer
    scaler:       MinMaxScaler | None = None

    # populated by similarity_service on startup
    corpus_vectors = None

    # model metadata
    model_metrics: dict = {}
    model_trained_at: datetime | None = None


_registry = DataRegistry()


def get_registry() -> DataRegistry:
    return _registry


# ── Public entry point ────────────────────────────────────────────────────────

async def initialise_seed_data() -> None:
    """
    Called once on startup. Generates all four synthetic datasets and runs
    feature engineering. Results stored in the global DataRegistry.
    """
    np.random.seed(settings.RANDOM_SEED)

    _registry.df_courts = _generate_courts()
    _registry.df_judges = _generate_judges(_registry.df_courts)
    _registry.df_laws   = pd.DataFrame(LAWS_SEED)
    _registry.df_cases  = _generate_cases(
        _registry.df_courts, _registry.df_judges, _registry.df_laws
    )
    _apply_feature_engineering(_registry.df_courts)


# ── Private generators ────────────────────────────────────────────────────────

def _generate_courts() -> pd.DataFrame:
    states  = list(STATE_CITY_MAP.keys())
    records = []
    court_id = 1

    courts_per_state = settings.SEED_COURTS // len(states)
    remainder        = settings.SEED_COURTS % len(states)

    for i, state in enumerate(states):
        cities = STATE_CITY_MAP[state]
        n      = courts_per_state + (1 if i < remainder else 0)
        for j in range(n):
            city       = cities[j % len(cities)]
            court_type = np.random.choice(COURT_TYPES, p=[0.55, 0.25, 0.15, 0.05])
            judge_strength        = int(np.random.randint(5, 50))
            pending_cases         = int(np.random.randint(500, 50_000))
            monthly_filing_rate   = int(np.random.randint(50, 800))
            monthly_disposal_rate = int(np.random.randint(30, 700))
            avg_disposal_time_days= int(np.random.randint(90, 900))
            infrastructure_score  = round(float(np.random.uniform(2, 10)), 2)
            digitization_level    = round(float(np.random.uniform(0.1, 1.0)), 2)

            records.append({
                "court_id":               f"COURT_{court_id:03d}",
                "court_name":             f"{city} {court_type}",
                "city":                   city,
                "state":                  state,
                "court_type":             court_type,
                "judge_strength":         judge_strength,
                "pending_cases":          pending_cases,
                "monthly_filing_rate":    monthly_filing_rate,
                "monthly_disposal_rate":  monthly_disposal_rate,
                "avg_disposal_time_days": avg_disposal_time_days,
                "infrastructure_score":   infrastructure_score,
                "digitization_level":     digitization_level,
            })
            court_id += 1

    return pd.DataFrame(records)


def _generate_judges(df_courts: pd.DataFrame) -> pd.DataFrame:
    records   = []
    judge_id  = 1
    n_judges  = settings.SEED_JUDGES
    court_ids = df_courts["court_id"].tolist()
    court_map = df_courts.set_index("court_id")[["court_name", "state"]].to_dict("index")

    for _ in range(n_judges):
        court_id   = str(np.random.choice(court_ids))
        court_info = court_map[court_id]
        first      = np.random.choice(["Rajiv", "Priya", "Amit", "Sunita", "Vikram",
                                        "Ananya", "Deepak", "Rekha", "Sanjay", "Kavita",
                                        "Mohan", "Geeta", "Arjun", "Lata", "Suresh"])
        last       = np.random.choice(["Sharma", "Verma", "Singh", "Kumar", "Gupta",
                                        "Patel", "Nair", "Reddy", "Rao", "Mehta",
                                        "Joshi", "Pillai", "Bose", "Das", "Iyer"])
        records.append({
            "judge_id":               f"JUDGE_{judge_id:04d}",
            "judge_name":             f"Hon. Justice {first} {last}",
            "court_id":               court_id,
            "court_name":             court_info["court_name"],
            "state":                  court_info["state"],
            "specialization":         str(np.random.choice(SPECIALIZATIONS)),
            "experience_years":       int(np.random.randint(5, 35)),
            "cases_handled":          int(np.random.randint(100, 5000)),
            "avg_judgment_time_days": int(np.random.randint(30, 730)),
            "reversal_rate":          round(float(np.random.uniform(0.01, 0.35)), 3),
            "bias_index":             round(float(np.random.uniform(0.0, 1.0)), 3),
            "rating_score":           round(float(np.random.uniform(3.0, 10.0)), 2),
        })
        judge_id += 1

    return pd.DataFrame(records)


def _generate_cases(
    df_courts: pd.DataFrame,
    df_judges: pd.DataFrame,
    df_laws:   pd.DataFrame,
) -> pd.DataFrame:
    records   = []
    n_cases   = settings.SEED_CASES
    law_ids   = df_laws["law_id"].tolist()
    court_ids = df_courts["court_id"].tolist()
    court_map = df_courts.set_index("court_id")[["court_name", "state", "court_type"]].to_dict("index")
    judge_map = df_judges.groupby("court_id")["judge_id"].apply(list).to_dict()

    base_date = datetime(2018, 1, 1)

    for i in range(n_cases):
        court_id   = str(np.random.choice(court_ids))
        court_info = court_map[court_id]
        court_judges = judge_map.get(court_id, [])
        judge_id   = str(np.random.choice(court_judges)) if court_judges else "JUDGE_0001"

        case_type  = str(np.random.choice(CASE_TYPES))
        status     = str(np.random.choice(
            CASE_STATUSES, p=[0.45, 0.30, 0.10, 0.10, 0.05]
        ))
        law_id     = str(np.random.choice(law_ids))
        days_filed = int(np.random.randint(0, 365 * 5))
        filing_dt  = base_date + timedelta(days=days_filed)
        days_pend  = int(np.random.randint(10, 2000))
        hearings   = int(np.random.randint(1, 50))
        complexity = round(float(np.random.uniform(1.0, 10.0)), 2)
        case_val   = round(float(np.random.uniform(0.5, 500.0)), 2)
        public_int = bool(np.random.random() < 0.15)

        # Generate case text
        tpl  = str(np.random.choice(_CASE_TEXT_TEMPLATES))
        act  = str(np.random.choice(_ACTS))
        text = tpl.format(act=act)
        city_part = court_info.get("court_name", court_id).lower().split()[0]
        text += f" court {city_part} {case_type.lower()} jurisdiction"

        # Clean text (minimal preprocessing)
        clean = re.sub(r"[^a-z\s]", "", text.lower())
        clean = re.sub(r"\s+", " ", clean).strip()

        # Binary outcome label
        outcome = 1 if status == "Decided" else 0

        # Case title
        plaintiffs = ["Ramesh Kumar", "Sita Devi", "State of India", "Union of India",
                      "Rajesh Singh", "Priya Sharma", "Municipal Corp", "Revenue Dept"]
        defendants = ["Suresh Gupta", "Ganesh Patel", "Private Ltd Co", "ABC Corporation",
                      "Sharma Brothers", "Tax Authority", "Land Revenue Dept", "accused"]
        plaintiff  = str(np.random.choice(plaintiffs))
        defendant  = str(np.random.choice(defendants))

        records.append({
            "case_id":           f"CASE_{i+1:06d}",
            "case_title":        f"{plaintiff} vs {defendant}",
            "case_number":       f"{court_id}/{filing_dt.year}/{i+1:04d}",
            "court_id":          court_id,
            "court_name":        court_info["court_name"],
            "state":             court_info["state"],
            "judge_id":          judge_id,
            "case_type":         case_type,
            "status":            status,
            "filing_date":       filing_dt.date(),
            "hearing_count":     hearings,
            "complexity_score":  complexity,
            "case_value_lakhs":  case_val,
            "days_pending":      days_pend,
            "public_interest_tag": public_int,
            "law_id":            law_id,
            "case_text":         text,
            "clean_text":        clean,
            "outcome":           outcome,
        })

    return pd.DataFrame(records)


# ── Feature engineering (modifies df_courts in-place) ────────────────────────

def _apply_feature_engineering(df_courts: pd.DataFrame) -> None:
    """
    Adds derived columns to df_courts and fits the MinMaxScaler.
    Preserved verbatim from JusticeGraph spec.
    """
    df_courts["backlog_rate"] = (
        df_courts["monthly_filing_rate"] - df_courts["monthly_disposal_rate"]
    ) / df_courts["judge_strength"]

    df_courts["utilization_rate"] = (
        df_courts["pending_cases"] / (df_courts["judge_strength"] * 100)
    )

    df_courts["efficiency_score"] = df_courts["monthly_disposal_rate"] / (
        df_courts["pending_cases"] + 1
    )

    df_courts["risk_factors"] = (
        df_courts["backlog_rate"] * 0.3
        + df_courts["utilization_rate"] * 0.3
        + (1 - df_courts["efficiency_score"]) * 0.2
        + (1 - df_courts["digitization_level"]) * 0.2
    )

    scaler = MinMaxScaler()
    df_courts["backlog_risk_score"] = scaler.fit_transform(
        df_courts[["risk_factors"]]
    )

    df_courts["risk_category"] = pd.cut(
        df_courts["backlog_risk_score"],
        bins=[0, 0.3, 0.6, 1.0],
        labels=["Low Risk", "Moderate Risk", "High Risk"],
        include_lowest=True,
    )

    _registry.scaler = scaler
