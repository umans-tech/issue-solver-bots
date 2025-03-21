import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# this is the Alembic Config object, which provides
# access to values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# e.g.:
# from myapp.db.models import Base
# target_metadata = Base.metadata
target_metadata = None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    We configure the context with just a URL
    and not an Engine. By skipping engine creation,
    we do not need a DBAPI to be available.
    """
    url = os.getenv("DB_URL", config.get_main_option("sqlalchemy.url"))
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Helper function that Alembic will run in a synchronous context."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    # Retrieve the URL either from env var or from alembic.ini
    # Make sure it's of the form: postgresql+asyncpg://user:pass@host/db
    config_section = config.get_section(config.config_ini_section, {})
    if not config_section:
        raise ValueError("No config section found")
    db_url = os.getenv("DB_URL", config_section["sqlalchemy.url"])

    # Create async engine
    connectable = create_async_engine(db_url, poolclass=pool.NullPool)

    async with connectable.connect() as async_connection:
        # Alembic’s migration context is synchronous, so we use run_sync.
        await async_connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    # Run the async function via asyncio.
    asyncio.run(run_migrations_online())
