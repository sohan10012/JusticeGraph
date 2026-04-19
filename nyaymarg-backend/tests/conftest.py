"""
tests/conftest.py — Pytest fixtures for NyayMarg test suite.
"""
from __future__ import annotations

import asyncio
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# ── Session-scoped event loop ─────────────────────────────────────────────────
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ── Initialise seed data + models once per test session ───────────────────────
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_data():
    from app.data.seed import initialise_seed_data
    from app.ml.loader import load_or_train_models
    await initialise_seed_data()
    await load_or_train_models()

    from app.services.similarity_service import SimilarityService
    SimilarityService().build_index()


# ── In-memory SQLite for DB tests ────────────────────────────────────────────
@pytest_asyncio.fixture(scope="session")
async def db_engine():
    from sqlalchemy.ext.asyncio import create_async_engine
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    from app.database import create_tables
    import app.database
    _orig = app.database.engine
    app.database.engine = engine
    await create_tables()
    yield engine
    app.database.engine = _orig
    await engine.dispose()


# ── HTTP client ───────────────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def client():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email":     "pytest@nyaymarg.in",
        "password":  "Test@1234",
        "full_name": "Pytest User",
        "role":      "researcher",
    })
    if resp.status_code == 409:
        resp = await client.post("/api/v1/auth/login", json={
            "email":    "pytest@nyaymarg.in",
            "password": "Test@1234",
        })
    token = resp.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}
