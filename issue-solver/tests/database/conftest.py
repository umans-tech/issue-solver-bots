import os
from typing import Any, Generator

import pytest
import pytest_asyncio
from alembic.command import downgrade, upgrade
from alembic.config import Config
from issue_solver.events.event_store import EventStore
from issue_solver.webapi.dependencies import init_event_store
from testcontainers.postgres import PostgresContainer
from tests.fixtures import ALEMBIC_INI_LOCATION, MIGRATIONS_PATH


@pytest.fixture(scope="module")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """Start a PostgreSQL container."""
    postgres_container = PostgresContainer(image="postgres:17.4-alpine")
    postgres_container.start()
    yield postgres_container

    postgres_container.stop()


@pytest.fixture
def run_migrations(postgres_container) -> Generator[None, Any, None]:
    """Run migrations on a PostgreSQL container."""
    config = Config(ALEMBIC_INI_LOCATION)
    db_url = f"postgresql+asyncpg://{postgres_container.username}:{postgres_container.password}@{postgres_container.get_container_host_ip()}:{postgres_container.get_exposed_port(5432)}/{postgres_container.dbname}"
    os.environ["DATABASE_URL"] = db_url
    config.set_section_option(
        section="alembic",
        name="script_location",
        value=MIGRATIONS_PATH,
    )
    upgrade(config, "head")
    yield
    downgrade(config, "base")


@pytest_asyncio.fixture(scope="function")
async def event_store(
    postgres_container: PostgresContainer, run_migrations
) -> EventStore:
    """Initialize and return an EventStore instance."""
    store = await init_event_store()
    return store
