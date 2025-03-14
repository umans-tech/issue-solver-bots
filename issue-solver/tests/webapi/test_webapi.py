import json
import os
from typing import Generator, Any

import boto3
import pytest
from fastapi.testclient import TestClient
from pytest_httpserver import HTTPServer
from testcontainers.localstack import LocalStackContainer

from issue_solver.webapi.main import app

CREATED_VECTOR_STORE_ID = "vs_abc123"


def test_connect_repository_returns_201_and_publishes_code_repository_connected_event(
    api_client, sqs_client, sqs_queue
):
    # Given
    repo_url = "https://github.com/test/repo"
    repo_access_token = "test-access-token"

    # When
    response = api_client.post(
        "/repositories/", json={"url": repo_url, "access_token": repo_access_token}
    )

    # Then
    assert response.status_code == 201
    data = response.json()
    assert data["url"] == repo_url
    assert "process_id" in data
    assert data["knowledge_base_id"] == CREATED_VECTOR_STORE_ID
    # Verify message was sent to SQS
    queue_url = sqs_queue["queue_url"]
    messages = sqs_client.receive_message(
        QueueUrl=queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=1
    )
    assert "Messages" in messages
    message_body = json.loads(messages["Messages"][0]["Body"])
    assert message_body["url"] == repo_url
    assert message_body["access_token"] == repo_access_token
    assert message_body["process_id"] == data["process_id"]
    assert message_body["knowledge_base_id"] == CREATED_VECTOR_STORE_ID


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
def sqs_client(localstack, aws_credentials):
    """Create and return an SQS client."""
    return boto3.client(
        "sqs",
        endpoint_url=localstack["endpoint_url"],
        region_name=aws_credentials["region"],
        aws_access_key_id=aws_credentials["access_key"],
        aws_secret_access_key=aws_credentials["secret_key"],
    )


@pytest.fixture
def sqs_queue(sqs_client):
    """Create a test SQS queue."""
    queue_name = "test-repo-queue"
    queue_response = sqs_client.create_queue(QueueName=queue_name)
    queue_url = queue_response["QueueUrl"]

    os.environ["PROCESS_QUEUE_URL"] = queue_url

    return {"queue_url": queue_url, "queue_name": queue_name}


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
def api_client(aws_credentials, sqs_queue, mock_openai) -> TestClient:
    """Create and return a FastAPI TestClient."""
    return TestClient(app)
