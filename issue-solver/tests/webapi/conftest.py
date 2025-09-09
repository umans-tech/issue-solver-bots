import asyncio
import os
import time
from datetime import datetime
from typing import Any, Generator

import asyncpg
import boto3
import pytest
import pytest_asyncio
from alembic.command import downgrade, upgrade
from alembic.config import Config
from pytest_httpserver import HTTPServer
from redis import Redis
from starlette.testclient import TestClient
from testcontainers.localstack import LocalStackContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from tests.controllable_clock import ControllableClock
from tests.fixtures import (
    ALEMBIC_INI_LOCATION,
    MIGRATIONS_PATH,
    NoopGitValidationService,
)

from issue_solver.agents.agent_message_store import AgentMessageStore
from issue_solver.webapi.dependencies import (
    get_clock,
    get_validation_service,
    init_agent_message_store,
)
from issue_solver.webapi.main import app

CREATED_VECTOR_STORE_ID = "vs_abc123"
DEFAULT_CURRENT_TIME = datetime.fromisoformat("2022-01-01T00:00:00")


@pytest.fixture(scope="module")
def localstack() -> Generator[dict[str, str], None, None]:
    """Start LocalStack container with SQS service."""
    localstack_container = LocalStackContainer(
        "localstack/localstack:latest"
    ).with_services("sqs")
    localstack_container.start()

    endpoint_url = localstack_container.get_url()
    yield {"endpoint_url": endpoint_url}

    localstack_container.stop()


@pytest.fixture
def aws_credentials(localstack) -> dict[str, str]:
    """Set and return AWS credentials."""
    credentials = {
        "region": "eu-west-3",
        "access_key": "test",
        "secret_key": "test",
    }

    os.environ["AWS_REGION"] = credentials["region"]
    os.environ["AWS_ACCESS_KEY_ID"] = credentials["access_key"]
    os.environ["AWS_SECRET_ACCESS_KEY"] = credentials["secret_key"]
    os.environ["AWS_DEFAULT_REGION"] = credentials["region"]
    os.environ["AWS_ENDPOINT_URL"] = localstack["endpoint_url"]

    return credentials


@pytest.fixture
def sqs_client(localstack, aws_credentials) -> Generator[boto3.client, Any, None]:
    """Create and return an SQS client."""
    yield boto3.client(
        "sqs",
        endpoint_url=localstack["endpoint_url"],
        region_name=aws_credentials["region"],
        aws_access_key_id=aws_credentials["access_key"],
        aws_secret_access_key=aws_credentials["secret_key"],
    )


@pytest.fixture
def sqs_queue(sqs_client) -> Generator[dict[str, str], Any, None]:
    """Create a test SQS queue."""
    queue_name = "test-repo-queue"
    queue_response = sqs_client.create_queue(QueueName=queue_name)
    queue_url = queue_response["QueueUrl"]

    os.environ["PROCESS_QUEUE_URL"] = queue_url

    yield {"queue_url": queue_url, "queue_name": queue_name}

    sqs_client.delete_queue(QueueUrl=queue_url)


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
def db_url(postgres_container) -> str:
    """Return the database URL for the PostgreSQL container."""
    return f"postgresql+asyncpg://{postgres_container.username}:{postgres_container.password}@{postgres_container.get_container_host_ip()}:{postgres_container.get_exposed_port(5432)}/{postgres_container.dbname}"


@pytest.fixture
def run_migrations(db_url) -> Generator[None, Any, None]:
    """Run migrations on a PostgreSQL container."""
    config = Config(ALEMBIC_INI_LOCATION)
    os.environ["DATABASE_URL"] = db_url
    config.set_section_option(
        section="alembic",
        name="script_location",
        value=MIGRATIONS_PATH,
    )
    upgrade(config, "head")
    yield
    downgrade(config, "base")


@pytest.fixture
def mock_openai(httpserver: HTTPServer) -> Generator[HTTPServer, Any, None]:
    """Mock the OpenAI client and its vector_stores methods."""
    os.environ["OPENAI_BASE_URL"] = httpserver.url_for("/v1")
    os.environ["OPENAI_API_KEY"] = "test-api-key"
    httpserver.expect_request("/v1/vector_stores", method="POST").respond_with_json(
        {
            "id": CREATED_VECTOR_STORE_ID,
            "object": "vector_store",
            "created_at": 1699061776,
            "name": "Support FAQ",
            "bytes": 139920,
            "file_counts": {
                "in_progress": 0,
                "completed": 3,
                "failed": 0,
                "cancelled": 0,
                "total": 3,
            },
        },
        status=200,
    )

    yield httpserver


@pytest.fixture
def time_under_control() -> ControllableClock:
    return ControllableClock(DEFAULT_CURRENT_TIME)


@pytest.fixture
def repo_validation_under_control() -> NoopGitValidationService:
    return NoopGitValidationService()


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
def redis_client(
    set_redis_url,
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


@pytest.fixture
def api_client(
    aws_credentials,
    sqs_queue,
    mock_openai,
    time_under_control,
    run_migrations,
    set_redis_url,
    repo_validation_under_control,
) -> Generator[TestClient, Any, None]:
    app.dependency_overrides[get_clock] = lambda: time_under_control
    app.dependency_overrides[get_validation_service] = (
        lambda: repo_validation_under_control
    )
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def receive_event_message(sqs_client, sqs_queue):
    return sqs_client.receive_message(
        QueueUrl=sqs_queue["queue_url"], MaxNumberOfMessages=1, WaitTimeSeconds=1
    )
