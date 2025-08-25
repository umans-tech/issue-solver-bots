import asyncio
import os
import time
from typing import Any, Generator

import asyncpg
import pytest
import pytest_asyncio
from alembic.command import downgrade, upgrade
from alembic.config import Config
from testcontainers.redis import RedisContainer

from issue_solver.agents.agent_message_store import AgentMessageStore
from issue_solver.database.init_event_store import extract_direct_database_url
from issue_solver.events.event_store import EventStore
from issue_solver.factories import init_event_store
from issue_solver.webapi.dependencies import init_agent_message_store
from testcontainers.postgres import PostgresContainer
from tests.fixtures import ALEMBIC_INI_LOCATION, MIGRATIONS_PATH


@pytest.fixture(scope="module")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """Start a PostgreSQL container."""
    with PostgresContainer(image="postgres:17.4-alpine") as postgres_container:
        db_url = f"postgresql://{postgres_container.username}:{postgres_container.password}@{postgres_container.get_container_host_ip()}:{postgres_container.get_exposed_port(5432)}/{postgres_container.dbname}"
        wait_for_postgres(db_url)
        yield postgres_container


def wait_for_postgres(db_url: str, timeout: int = 5) -> None:
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            asyncio.run(_check_connection(db_url))
            return
        except Exception:
            time.sleep(1)
    raise TimeoutError(f"PostgreSQL n'est pas prêt après {timeout} secondes")


async def _check_connection(db_url: str) -> None:
    conn = await asyncpg.connect(db_url)
    await conn.execute("SELECT 1")
    await conn.close()


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
    store = await init_event_store(database_url=extract_direct_database_url())
    return store


@pytest.fixture(scope="module")
def redis_container() -> Generator[Any, None, None]:
    """Start a Redis container."""
    with RedisContainer("redis:7.2-alpine") as redis_container:
        yield redis_container


@pytest.fixture(scope="module")
def set_redis_url(redis_container: RedisContainer) -> None:
    """Set the REDIS_URL environment variable."""
    os.environ["REDIS_URL"] = (
        f"redis://{redis_container.get_container_host_ip()}:{redis_container.get_exposed_port(6379)}"
    )


@pytest_asyncio.fixture(scope="function")
async def agent_message_store(
    set_redis_url,
    run_migrations,
    redis_container: RedisContainer,
) -> AgentMessageStore:
    """Initialize and return an AgentMessageStore instance."""
    return await init_agent_message_store()


@pytest.fixture(scope="function")
def generated_encryption_key() -> str:
    """Generate a random encryption key for testing."""
    return "hp6ocOWdpR69r8lRUzci2cCSjwmqpntBojmnhaIJD_M="
