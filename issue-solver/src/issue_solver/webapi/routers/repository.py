import logging
import os
import uuid
from typing import Annotated

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, Depends
from openai import OpenAI

from issue_solver.clock import Clock
from issue_solver.events.domain import CodeRepositoryConnected
from issue_solver.events.event_store import InMemoryEventStore
from issue_solver.events.serializable_records import serialize
from issue_solver.webapi.dependencies import get_event_store, get_logger, get_clock
from issue_solver.webapi.payloads import ConnectRepositoryRequest

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post("/", status_code=201)
async def connect_repository(
    connect_repository_request: ConnectRepositoryRequest,
    event_store: Annotated[InMemoryEventStore, Depends(get_event_store)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(lambda: get_logger("issue_solver.webapi.routers.repository.connect")),
    ],
    clock: Annotated[Clock, Depends(get_clock)],
):
    """Connect to a code repository."""
    process_id = str(uuid.uuid4())
    logger.info(f"Creating new repository connection with process ID: {process_id}")

    client = OpenAI()
    repo_name = connect_repository_request.url.split("/")[-1]
    logger.info(f"Creating vector store for repository: {repo_name}")

    vector_store = client.vector_stores.create(name=repo_name)
    event = CodeRepositoryConnected(
        occurred_at=clock.now(),
        url=connect_repository_request.url,
        access_token=connect_repository_request.access_token,
        user_id=connect_repository_request.user_id,
        space_id=connect_repository_request.space_id,
        knowledge_base_id=vector_store.id,
        process_id=process_id,
    )
    await event_store.append(process_id, event)

    # Get a logger specifically for the publish function
    publish_logger = get_logger("issue_solver.webapi.routers.repository.publish")
    publish(event, publish_logger)

    logger.info(
        f"Repository connection created successfully with process ID: {process_id}"
    )
    return {
        "url": event.url,
        "process_id": event.process_id,
        "knowledge_base_id": event.knowledge_base_id,
    }


def publish(
    event: CodeRepositoryConnected, logger: logging.Logger | logging.LoggerAdapter
) -> None:
    """Publish a CodeRepositoryConnected event to SQS."""
    try:
        logger.info(f"Publishing event for process ID: {event.process_id}")
        sqs_client = boto3.client(
            "sqs", region_name=os.environ.get("AWS_REGION", "eu-west-3")
        )

        queue_url = os.environ.get("PROCESS_QUEUE_URL")
        if not queue_url:
            raise ValueError("PROCESS_QUEUE_URL environment variable not set")

        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=serialize(event).model_dump_json(),
        )

        logger.info(
            f"Published process ID {event.process_id} successfully with message ID {response['MessageId']}"
        )

    except (ClientError, ValueError) as e:
        logger.error(f"Failed to publish process ID {event.process_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to send message to SQS: {str(e)}"
        )
