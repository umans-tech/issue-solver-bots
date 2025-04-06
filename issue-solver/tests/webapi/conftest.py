import asyncio
import os
import time
from datetime import datetime
from typing import Any, Generator

import asyncpg
import boto3
import pytest
from alembic.command import downgrade, upgrade
from alembic.config import Config
from issue_solver.git_operations.git_helper import NoopGitValidationService
from issue_solver.webapi.dependencies import get_clock, get_validation_service
from issue_solver.webapi.main import app
from pytest_httpserver import HTTPServer
from starlette.testclient import TestClient
from testcontainers.localstack import LocalStackContainer
from testcontainers.postgres import PostgresContainer
from tests.controllable_clock import ControllableClock
from tests.fixtures import ALEMBIC_INI_LOCATION, MIGRATIONS_PATH

# Set testing environment variable to enable test-friendly behavior
os.environ["TESTING"] = "true"

CREATED_VECTOR_STORE_ID = "vs_abc123"
DEFAULT_CURRENT_TIME = datetime.fromisoformat("2022-01-01T00:00:00")


# Create a function to get a NoopGitValidationService for tests
def get_test_validation_service():
    return NoopGitValidationService()


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
def api_client(
    aws_credentials, sqs_queue, mock_openai, time_under_control, run_migrations
) -> Generator[TestClient, Any, None]:
    """Create and return a FastAPI TestClient."""
    # Override clock dependency
    app.dependency_overrides[get_clock] = lambda: time_under_control

    # Override git validation service dependency - always use NoopGitValidationService for tests
    app.dependency_overrides[get_validation_service] = get_test_validation_service

    with TestClient(app) as client:
        yield client

    # Clean up overrides after the test
    app.dependency_overrides.clear()
