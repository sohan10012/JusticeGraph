"""
tests/integration/test_analytics.py — Integration tests for analytics endpoints.
"""
import pytest


@pytest.mark.asyncio
async def test_overview(client):
    r = await client.get("/api/v1/analytics/overview")
    assert r.status_code == 200
    body = r.json()
    assert body["total_courts"] == 120
    assert body["total_judges"] == 300
    assert body["total_cases"]  == 7000


@pytest.mark.asyncio
async def test_outcomes(client):
    r = await client.get("/api/v1/analytics/outcomes")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, dict)
    assert sum(body.values()) == 7000


@pytest.mark.asyncio
async def test_case_types(client):
    r = await client.get("/api/v1/analytics/case-types")
    assert r.status_code == 200
    body = r.json()
    # 'Criminal', 'Civil', etc.
    assert len(body) >= 5


@pytest.mark.asyncio
async def test_state_heatmap(client):
    r = await client.get("/api/v1/analytics/state-heatmap")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert len(body) == 18  # 18 states
    assert "state" in body[0]
    assert "case_count" in body[0]


@pytest.mark.asyncio
async def test_model_performance(client):
    r = await client.get("/api/v1/analytics/model-performance")
    assert r.status_code == 200
    body = r.json()
    assert "rf_model" in body or "status" in body


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert body["models"]["rf_model"] is True
    assert body["models"]["lr_model"] is True
