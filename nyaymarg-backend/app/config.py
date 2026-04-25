"""
app/config.py — NyayMarg centralised settings via pydantic-settings.
"""
from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "NyayMarg API"
    VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"  # development | staging | production

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://nyaymarg:password@localhost/nyaymarg"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ── Auth ─────────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440   # 24 h
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── Redis + Celery ────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── ML ────────────────────────────────────────────────────────────────────
    MODEL_ARTEFACTS_DIR: str = "./app/ml/artefacts"
    DEFAULT_N_ESTIMATORS: int = 200
    DEFAULT_SIMILARITY_TOP_N: int = 5
    MIN_PREDICTION_ACCURACY: float = 0.75
    RFC_WEIGHT: float = 0.65          # ensemble weighting
    LR_WEIGHT: float = 0.35

    # ── Upload ────────────────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 500
    ALLOWED_EXTENSIONS: list[str] = [".csv", ".json"]
    UPLOAD_DIR: str = "./uploads"

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # ── Seed Data ─────────────────────────────────────────────────────────────
    SEED_COURTS: int = 120
    SEED_JUDGES: int = 300
    SEED_CASES: int = 7000
    RANDOM_SEED: int = 42

    # ═══ External Legal APIs ═════════════════════════════════════════════════

    # ── Indian Kanoon API (api.indiankanoon.org) ──────────────────────────────
    IK_API_TOKEN: str = ""
    IK_API_BASE:  str = "https://api.indiankanoon.org"
    IK_ENABLED:   bool = False

    # ── kanoon.dev structured API ─────────────────────────────────────────────
    KANOON_DEV_API_KEY: str = ""
    KANOON_DEV_BASE:    str = "https://api.kanoon.dev/v1"
    KANOON_DEV_ENABLED: bool = False

    # ── ECIAPI — eCourts India API (eciapi.akshit.me) ─────────────────────────
    ECIAPI_BASE:    str  = "https://court-api.kleopatra.io"
    ECIAPI_ENABLED: bool = True

    # ── eCourtsIndia.com API (₹200 free credits) ──────────────────────────────
    ECOURTSINDIA_TOKEN:   str  = ""
    ECOURTSINDIA_BASE:    str  = "https://webapi.ecourtsindia.com/api"
    ECOURTSINDIA_ENABLED: bool = False

    # ── data.gov.in OGD API ───────────────────────────────────────────────────
    DATA_GOV_API_KEY: str  = ""
    DATA_GOV_BASE:    str  = "https://api.data.gov.in/resource"
    DATA_GOV_ENABLED: bool = False

    # ── DDL Judicial Dataset (bulk download, Open DB License) ─────────────────
    DDL_DATASET_URL: str  = "https://www.devdatalab.org/judicial-data"
    DDL_LOCAL_PATH:  str  = "./data/ddl_judicial"
    DDL_ENABLED:     bool = False

    # ── CourtListener REST API v4 (US legal data, free token) ─────────────────
    COURTLISTENER_TOKEN:   str  = ""
    COURTLISTENER_BASE:    str  = "https://www.courtlistener.com/api/rest/v4"
    COURTLISTENER_ENABLED: bool = False

    # ── Global external API settings ───────────────────────────────────────────
    EXTERNAL_API_TIMEOUT_SECONDS:   int = 15
    EXTERNAL_API_MAX_RETRIES:       int = 3
    EXTERNAL_API_CACHE_TTL_SECONDS: int = 3600   # 1-hour response cache
    EXTERNAL_API_RATE_LIMIT_PER_MIN:int = 30

    @model_validator(mode="after")
    def validate_api_activation(self) -> "Settings":
        """
        Auto-enables APIs if their respective tokens/keys are present.
        Ensures KANOON_DEV remains manual or gated by key presence.
        """
        # Auto-enable if token is present, but respect explicit True in .env
        if not self.IK_ENABLED:
            self.IK_ENABLED = bool(self.IK_API_TOKEN)
        
        if not self.ECOURTSINDIA_ENABLED:
            self.ECOURTSINDIA_ENABLED = bool(self.ECOURTSINDIA_TOKEN)
            
        if not self.DATA_GOV_ENABLED:
            self.DATA_GOV_ENABLED = bool(self.DATA_GOV_API_KEY)
            
        if not self.COURTLISTENER_ENABLED:
            self.COURTLISTENER_ENABLED = bool(self.COURTLISTENER_TOKEN)

        # Gated by key presence for KANOON_DEV
        if not self.KANOON_DEV_API_KEY:
            self.KANOON_DEV_ENABLED = False
        # If key is present and it wasn't already set to False explicitly, enable it
        elif self.KANOON_DEV_ENABLED is None: # Pydantic might default to False
             self.KANOON_DEV_ENABLED = True

        # Render provides postgres://; async SQLAlchemy expects postgresql+asyncpg://
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
        elif self.DATABASE_URL.startswith("postgresql://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

        return self

    model_config = {
        "env_file": str(Path(__file__).parent.parent / ".env"),
        "extra": "ignore"
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
