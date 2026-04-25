"""
app/database.py — Async SQLAlchemy engine + session factory.
"""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text

from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
    future=True,
    connect_args={
        "command_timeout": 60,
        "ssl": "require" if "render.com" in settings.DATABASE_URL else False,
        "server_settings": {
            "application_name": "nyaymarg_backend",
        }
    } if "postgres" in settings.DATABASE_URL else {}
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_tables() -> None:
    """Create all ORM tables. Called on startup (dev/test only — production uses Alembic)."""
    from app.models.base import Base  # noqa: F401 — side-effect imports
    import app.models.user           # noqa: F401
    import app.models.court          # noqa: F401
    import app.models.judge          # noqa: F401
    import app.models.case           # noqa: F401
    import app.models.prediction     # noqa: F401
    import app.models.bookmark       # noqa: F401
    import app.models.notification   # noqa: F401
    import app.models.chat_message   # noqa: F401
    import app.models.ml_model       # noqa: F401
    import app.models.dataset        # noqa: F401
    import app.models.audit_log      # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def check_db_connection() -> str:
    """Health-check helper — returns 'ok' or an error message."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return "ok"
    except Exception as exc:
        return f"error: {exc}"
