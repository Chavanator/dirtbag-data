"""Alembic environment for DirtBag Data.

- Online mode: connects using DIRTBAG_DATABASE_URL (or the YAML config).
- Offline mode (``alembic upgrade head --sql``): renders literal SQL without
  a database connection.

``target_metadata`` stays ``None`` until SQLAlchemy models land (Phase 2
models); migrations are hand-written and reviewed until then — autogenerate
must never edit historical migrations.
"""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make the package importable when running from a source checkout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from dirtbag_data.config import load_settings  # noqa: E402

try:
    db_url = os.environ.get("DIRTBAG_DATABASE_URL") or load_settings().database.url
except FileNotFoundError:
    db_url = os.environ.get("DIRTBAG_DATABASE_URL", "")

# ConfigParser interpolation: escape literal percent signs in URLs.
config.set_main_option("sqlalchemy.url", db_url.replace("%", "%%"))

target_metadata = None  # Phase 2: wire SQLAlchemy models here


def run_migrations_offline() -> None:
    context.configure(url=db_url, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
