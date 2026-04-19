"""
tests/unit/test_seed.py — Unit tests for data generation.
"""
import pytest
from app.data.seed import get_registry


def test_courts_generated():
    df = get_registry().df_courts
    assert df is not None
    assert len(df) == 120
    assert "court_id" in df.columns
    assert "backlog_risk_score" in df.columns
    assert "risk_category" in df.columns


def test_judges_generated():
    df = get_registry().df_judges
    assert df is not None
    assert len(df) == 300
    assert "judge_id" in df.columns
    assert "rating_score" in df.columns


def test_cases_generated():
    df = get_registry().df_cases
    assert df is not None
    assert len(df) == 7000
    assert "case_id" in df.columns
    assert "clean_text" in df.columns
    assert "outcome" in df.columns
    # outcome must be binary
    assert set(df["outcome"].unique()).issubset({0, 1})


def test_laws_generated():
    df = get_registry().df_laws
    assert df is not None
    assert len(df) == 9
    assert "law_id" in df.columns


def test_feature_engineering():
    df = get_registry().df_courts
    assert "backlog_rate" in df.columns
    assert "utilization_rate" in df.columns
    assert "efficiency_score" in df.columns
    # Risk scores in [0, 1]
    assert df["backlog_risk_score"].min() >= 0
    assert df["backlog_risk_score"].max() <= 1.001
