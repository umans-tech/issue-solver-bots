from typing import Generator, Any

import pytest
from redis import Redis
from testcontainers.redis import RedisContainer


@pytest.fixture(scope="module")
def redis_container() -> Generator[Any, None, None]:
    """Start a Redis container."""
    with RedisContainer("redis:7.2-alpine") as redis_container:
        yield redis_container


@pytest.fixture(scope="function")
def redis_client(
    redis_container: RedisContainer,
) -> Generator[Redis, None, None]:
    redis_client = Redis(
        host=redis_container.get_container_host_ip(),
        port=int(redis_container.get_exposed_port(6379)),
        decode_responses=True,
    )
    yield redis_client
    redis_client.flushall()
    redis_client.close()
