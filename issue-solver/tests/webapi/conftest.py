import os
from datetime import datetime
from typing import Generator, Any

import boto3
import pytest
from alembic.command import upgrade, downgrade
from alembic.config import Config
from pytest_httpserver import HTTPServer
from starlette.testclient import TestClient
from testcontainers.localstack import LocalStackContainer
from testcontainers.postgres import PostgresContainer
from tests.controllable_clock import ControllableClock

from tests.fixtures import ALEMBIC_INI_LOCATION, MIGRATIONS_PATH
from issue_solver.webapi.dependencies import get_clock
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
    app.dependency_overrides[get_clock] = lambda: time_under_control
    with TestClient(app) as client:
        yield client
