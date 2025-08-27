import asyncio
import time
from typing import Generator

import asyncpg
import pytest
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="module")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """Start a PostgreSQL container."""
    with PostgresContainer(image="postgres:17.4-alpine") as postgres_container:
        db_url = extract_db_url(postgres_container)
        wait_for_postgres(db_url)
        yield postgres_container


@pytest.fixture(scope="module")
def database_url(postgres_container: PostgresContainer) -> str:
    return extract_db_url(postgres_container)


def extract_db_url(postgres_container: PostgresContainer) -> str:
    return f"postgresql://{postgres_container.username}:{postgres_container.password}@{postgres_container.get_container_host_ip()}:{postgres_container.get_exposed_port(5432)}/{postgres_container.dbname}"


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
