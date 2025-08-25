import asyncio
import os
import time
from typing import Any, Generator

import asyncpg
import boto3
import pytest
import pytest_asyncio
from alembic.command import downgrade, upgrade
from alembic.config import Config
from testcontainers.localstack import LocalStackContainer

from issue_solver.database.init_event_store import extract_direct_database_url
from issue_solver.events.event_store import EventStore
from testcontainers.postgres import PostgresContainer
from tests.fixtures import ALEMBIC_INI_LOCATION, MIGRATIONS_PATH

from issue_solver.factories import init_event_store
from issue_solver.queueing.sqs_events_publishing import SQSQueueingEventStore


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
    postgres_container: PostgresContainer, run_migrations, sqs_queue
) -> EventStore:
    """Initialize and return an EventStore instance."""
    store = await init_event_store(
        database_url=extract_direct_database_url(),
        queue_url=os.environ["PROCESS_QUEUE_URL"],
    )
    return SQSQueueingEventStore(store, sqs_queue.get("queue_url"))


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


def receive_event_message(sqs_client, sqs_queue):
    return sqs_client.receive_message(
        QueueUrl=sqs_queue["queue_url"], MaxNumberOfMessages=1, WaitTimeSeconds=1
    )
