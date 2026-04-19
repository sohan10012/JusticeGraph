"""
app/main.py — NyayMarg FastAPI application factory.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

import os
from app.config import settings
from app.core.logging import configure_logging
from app.database import create_tables
from app.data.seed import initialise_seed_data
from app.ml.loader import load_or_train_models, get_model_registry
from app.utils.fs import ensure_runtime_dirs

configure_logging()
logger = structlog.get_logger("nyaymarg")
limiter = Limiter(key_func=get_remote_address)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────
    logger.info("nyaymarg.startup", version=settings.VERSION, env=settings.ENVIRONMENT)

    # Ensure dirs exist (prevents PermissionError on Render)
    ensure_runtime_dirs()

    await create_tables()
    logger.info("nyaymarg.db_ready")

    await initialise_seed_data()
    logger.info("nyaymarg.seed_data_ready")

    # DDL real-data override (when DDL_ENABLED=True and files are present)
    if settings.DDL_ENABLED:
        from app.data.ddl_loader import load_ddl_dataset
        loaded = await load_ddl_dataset()
        logger.info("nyaymarg.ddl_dataset", loaded=loaded)

    # Skip heavy training on Render free tier
    if os.getenv("SKIP_MODEL_TRAINING", "False") != "True":
        await load_or_train_models()
        logger.info("nyaymarg.ml_ready")
    else:
        logger.info("nyaymarg.ml_skipped_on_boot")

    # Build cosine similarity index
    from app.services.similarity_service import SimilarityService
    SimilarityService().build_index()
    logger.info("nyaymarg.similarity_index_ready")

    logger.info("nyaymarg.ready")
    yield

    # ── Shutdown ─────────────────────────────────────────────
    logger.info("nyaymarg.shutdown")


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="NyayMarg API",
    description="""
## NyayMarg — AI-Powered Legal Case Analysis & Prediction System

Production-grade REST API for the Indian judicial analytics platform.

### Features
- 🎯 **Case outcome prediction** — RFC + Logistic Regression ensemble (65/35 weighting)
- 🔍 **Precedent discovery** — cosine similarity over 7,000+ indexed cases
- 📊 **Court & judge analytics** — risk maps, leaderboards, bias analysis
- 💬 **Intent-aware legal assistant** — rule-based chat with LLM-ready architecture
- 📂 **Dataset management** — upload CSV/JSON, trigger background retraining
- 📄 **PDF export** — prediction reports and full analytics via ReportLab
- 🌐 **External legal APIs** — Indian Kanoon, ECIAPI, kanoon.dev, CourtListener, data.gov.in

### Data
Powered by synthetic datasets (120 courts · 300 judges · 7,000 cases · 9 laws across 18 Indian
states) with optional real-data upgrades via DDL Judicial Dataset (81M cases) and live eCourts APIs.
    """,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten per-environment via config
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
from app.routers import (  # noqa: E402
    auth, courts, judges, cases, laws, predictions,
    analytics, similar, datasets, ml_models,
    chat, bookmarks, notifications, users,
)
from app.routers import external  # noqa: E402

PREFIX = "/api/v1"

# Core routers
app.include_router(auth.router,          prefix=f"{PREFIX}/auth",          tags=["Auth"])
app.include_router(courts.router,        prefix=f"{PREFIX}/courts",        tags=["Courts"])
app.include_router(judges.router,        prefix=f"{PREFIX}/judges",        tags=["Judges"])
app.include_router(cases.router,         prefix=f"{PREFIX}/cases",         tags=["Cases"])
app.include_router(laws.router,          prefix=f"{PREFIX}/laws",          tags=["Laws"])
app.include_router(predictions.router,   prefix=f"{PREFIX}/predict",       tags=["Predictions"])
app.include_router(analytics.router,     prefix=f"{PREFIX}/analytics",     tags=["Analytics"])
app.include_router(similar.router,       prefix=f"{PREFIX}/similar",       tags=["Precedents"])
app.include_router(datasets.router,      prefix=f"{PREFIX}/data",          tags=["Datasets"])
app.include_router(ml_models.router,     prefix=f"{PREFIX}/model",         tags=["ML Models"])
app.include_router(chat.router,          prefix=f"{PREFIX}/chat",          tags=["Chat"])
app.include_router(bookmarks.router,     prefix=f"{PREFIX}/bookmarks",     tags=["Bookmarks"])
app.include_router(notifications.router, prefix=f"{PREFIX}/notifications", tags=["Notifications"])
app.include_router(users.router,         prefix=f"{PREFIX}/users",         tags=["Users"])

# External Legal APIs
app.include_router(external.router,      prefix=f"{PREFIX}",               tags=["External Legal APIs"])


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"], summary="API health check")
async def health_check():
    """Returns DB, Redis, and ML model loaded status. Always unauthenticated."""
    from app.database import check_db_connection

    registry = get_model_registry()

    # Redis connectivity (optional)
    redis_status = "unknown"
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        r.ping()
        redis_status = "ok"
    except Exception as exc:
        redis_status = f"unavailable: {exc}"

    return {
        "status":    "healthy",
        "version":   settings.VERSION,
        "database":  await check_db_connection(),
        "redis":     redis_status,
        "models": {
            "rf_model":   registry.rf_model is not None,
            "lr_model":   registry.lr_model is not None,
            "vectorizer": registry.vectorizer is not None,
        },
        "external_apis": {
            "indian_kanoon":  settings.IK_ENABLED,
            "kanoon_dev":     settings.KANOON_DEV_ENABLED,
            "eciapi":         settings.ECIAPI_ENABLED,
            "ecourtsindia":   settings.ECOURTSINDIA_ENABLED,
            "data_gov":       settings.DATA_GOV_ENABLED,
            "ddl_dataset":    settings.DDL_ENABLED,
            "courtlistener":  settings.COURTLISTENER_ENABLED,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
