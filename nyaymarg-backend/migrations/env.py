"""
Alembic environment configuration for NyayMarg.
All ORM models are imported here so Alembic can autogenerate migrations.
"""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# ── Load app config ───────────────────────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings

# ── Import ALL models so Alembic sees them ───────────────────────────────────
from app.models.base import Base  # noqa: F401
import app.models.user            # noqa: F401
import app.models.court           # noqa: F401
import app.models.judge           # noqa: F401
import app.models.case            # noqa: F401
import app.models.prediction      # noqa: F401
import app.models.bookmark        # noqa: F401
import app.models.notification    # noqa: F401
import app.models.chat_message    # noqa: F401
import app.models.ml_model        # noqa: F401
import app.models.dataset         # noqa: F401
import app.models.audit_log       # noqa: F401

config          = context.config
target_metadata = Base.metadata

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url from app settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
