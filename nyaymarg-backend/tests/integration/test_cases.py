"""
tests/integration/test_cases.py — Integration tests for cases and search.
"""
import pytest


@pytest.mark.asyncio
async def test_list_cases(client):
    r = await client.get("/api/v1/cases/")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 7000
    assert len(data["items"]) == 20   # default page_size


@pytest.mark.asyncio
async def test_case_detail(client):
    r = await client.get("/api/v1/cases/CASE_000001")
    assert r.status_code == 200
    assert r.json()["case_id"] == "CASE_000001"


@pytest.mark.asyncio
async def test_case_not_found(client):
    r = await client.get("/api/v1/cases/CASE_XXXXXX")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_case_search(client):
    r = await client.get("/api/v1/cases/search?q=murder")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_case_summary(client):
    r = await client.get("/api/v1/cases/stats/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 7000
    assert "by_status" in body
    assert "by_type" in body


@pytest.mark.asyncio
async def test_pendency_stats(client):
    r = await client.get("/api/v1/cases/stats/pendency")
    assert r.status_code == 200
    body = r.json()
    assert "distribution" in body
    assert "avg_days_pending" in body


@pytest.mark.asyncio
async def test_similar_search(client):
    r = await client.post("/api/v1/similar/search", json={
        "query": "property dispute inheritance family law",
        "top_n": 5,
    })
    assert r.status_code == 200
    results = r.json()
    assert isinstance(results, list)
    assert len(results) <= 5
    for item in results:
        assert "case_id" in item
        assert "similarity_score" in item
        assert 0.0 <= item["similarity_score"] <= 1.0
