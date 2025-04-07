import logging
import os
import uuid
from typing import Annotated

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException
from issue_solver.clock import Clock
from issue_solver.events.domain import (
    AnyDomainEvent,
    CodeRepositoryConnected,
    RepositoryIndexationRequested,
)
from issue_solver.events.event_store import EventStore
from issue_solver.events.serializable_records import serialize
from issue_solver.git_operations.git_helper import (
    GitValidationError,
    GitValidationService,
)
from issue_solver.webapi.dependencies import (
    get_clock,
    get_event_store,
    get_logger,
    get_validation_service,
)
from issue_solver.webapi.payloads import ConnectRepositoryRequest
from openai import OpenAI

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post("/", status_code=201)
async def connect_repository(
    connect_repository_request: ConnectRepositoryRequest,
    event_store: Annotated[EventStore, Depends(get_event_store)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(lambda: get_logger("issue_solver.webapi.routers.repository.connect")),
    ],
    clock: Annotated[Clock, Depends(get_clock)],
    validation_service: Annotated[
        GitValidationService, Depends(get_validation_service)
    ],
) -> dict[str, str]:
    """Connect to a code repository."""
    _validate_repository_access(connect_repository_request, logger, validation_service)

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


def _validate_repository_access(connect_repository_request, logger, validation_service):
    try:
        validation_service.validate_repository_access(
            connect_repository_request.url,
            connect_repository_request.access_token,
            logger,
        )
    except GitValidationError as e:
        logger.error(f"Repository validation failed: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{knowledge_base_id}", status_code=200)
async def index_new_changes(
    knowledge_base_id: str,
    event_store: Annotated[EventStore, Depends(get_event_store)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(lambda: get_logger("issue_solver.webapi.routers.repository.index")),
    ],
    clock: Annotated[Clock, Depends(get_clock)],
) -> dict[str, str]:
    """Index new changes in the code repository."""
    logger.info(f"Indexing new changes for knowledge base ID: {knowledge_base_id}")

    # Find the repository connection with the given knowledge_base_id
    repository_connections = await event_store.find(
        {"knowledge_base_id": knowledge_base_id}, CodeRepositoryConnected
    )

    # Check if any repository was found
    if not repository_connections:
        logger.error(f"No repository found with knowledge base ID: {knowledge_base_id}")
        raise HTTPException(
            status_code=404,
            detail=f"No repository found with knowledge base ID: {knowledge_base_id}",
        )

    event = RepositoryIndexationRequested(
        occurred_at=clock.now(),
        knowledge_base_id=knowledge_base_id,
        process_id=repository_connections[0].process_id,
        user_id="unknown",
    )
    await event_store.append(event.process_id, event)
    logger.info(
        f"New changes indexed successfully for knowledge base ID: {knowledge_base_id}"
    )
    # Publish the event to SQS
    publish_logger = get_logger("issue_solver.webapi.routers.repository.publish")
    publish(event, publish_logger)
    logger.info(
        f"Published indexation request for knowledge base ID: {knowledge_base_id}"
    )

    return {"message": "New changes indexed successfully"}


def publish(
    event: AnyDomainEvent, logger: logging.Logger | logging.LoggerAdapter
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
