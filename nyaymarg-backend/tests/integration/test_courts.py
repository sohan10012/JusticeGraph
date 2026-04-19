"""
tests/integration/test_courts.py — Integration tests for court endpoints.
"""
import pytest


@pytest.mark.asyncio
async def test_list_courts(client):
    r = await client.get("/api/v1/courts/")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) > 0
    assert data["total"] == 120


@pytest.mark.asyncio
async def test_list_courts_filter_state(client):
    r = await client.get("/api/v1/courts/?state=Maharashtra")
    assert r.status_code == 200
    items = r.json()["items"]
    for item in items:
        assert item["state"] == "Maharashtra"


@pytest.mark.asyncio
async def test_court_detail(client):
    r = await client.get("/api/v1/courts/COURT_001")
    assert r.status_code == 200
    body = r.json()
    assert body["court_id"] == "COURT_001"
    assert "backlog_risk_score" in body


@pytest.mark.asyncio
async def test_court_not_found(client):
    r = await client.get("/api/v1/courts/COURT_NOPE")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_predict_court_risk(client):
    r = await client.post("/api/v1/courts/predict-risk", json={
        "judge_strength":         15,
        "pending_cases":          12000,
        "monthly_filing_rate":    400,
        "monthly_disposal_rate":  280,
        "avg_disposal_time_days": 540,
        "infrastructure_score":   6.2,
        "digitization_level":     0.55,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["risk_label"] in ("Low Risk", "Moderate Risk", "High Risk")
    assert 0.0 <= body["risk_probability"] <= 1.0
    assert len(body["contributing_factors"]) == 7


@pytest.mark.asyncio
async def test_court_summary(client):
    r = await client.get("/api/v1/courts/stats/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["total_courts"] == 120
    assert "by_state" in body
    assert "by_risk_category" in body


@pytest.mark.asyncio
async def test_risk_map(client):
    r = await client.get("/api/v1/courts/stats/risk-map")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 120
    assert "backlog_risk_score" in items[0]
