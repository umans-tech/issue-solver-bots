# pytest fixture returning emulated s3 using localstack
import os
from typing import Generator, Any

import boto3
import pytest
from botocore.client import BaseClient
from testcontainers.localstack import LocalStackContainer

from issue_solver.worker.documenting.knowledge_repository import KnowledgeRepository
from issue_solver.worker.documenting.s3_knowledge_repository import (
    S3KnowledgeRepository,
)

KNOWLEDGE_BUCKET = "knowledge-bucket"


@pytest.fixture(scope="module")
def localstack() -> Generator[dict[str, str], None, None]:
    """Start a LocalStack container with S3 service."""
    localstack_container = LocalStackContainer(
        "localstack/localstack:latest"
    ).with_services("s3")
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
def s3_client(
    localstack: dict[str, str], aws_credentials: dict[str, str]
) -> Generator[BaseClient, None, None]:
    s3_client = boto3.client(
        "s3",
        endpoint_url=localstack["endpoint_url"],
        region_name=aws_credentials["region"],
        aws_access_key_id=aws_credentials["access_key"],
        aws_secret_access_key=aws_credentials["secret_key"],
    )

    yield s3_client


@pytest.fixture
def create_s3_bucket(s3_client, aws_credentials) -> Generator[Any, Any, None]:
    yield s3_client.create_bucket(
        Bucket=KNOWLEDGE_BUCKET,
        CreateBucketConfiguration={"LocationConstraint": aws_credentials["region"]},
    )
    # Cleanup: delete all objects and the bucket
    response = s3_client.list_objects_v2(Bucket=KNOWLEDGE_BUCKET)
    if "Contents" in response:
        for obj in response["Contents"]:
            s3_client.delete_object(Bucket=KNOWLEDGE_BUCKET, Key=obj["Key"])
    s3_client.delete_bucket(Bucket=KNOWLEDGE_BUCKET)


@pytest.fixture(scope="function")
def knowledge_repository(s3_client, create_s3_bucket) -> KnowledgeRepository:
    return S3KnowledgeRepository(s3_client, KNOWLEDGE_BUCKET)
