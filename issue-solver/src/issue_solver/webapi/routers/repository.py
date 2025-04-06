import logging
import os
import uuid
from typing import Annotated
from pathlib import Path
import tempfile

import boto3
import git.exc
from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, Depends
from openai import OpenAI

from issue_solver.clock import Clock
from issue_solver.events.domain import (
    CodeRepositoryConnected,
    AnyDomainEvent,
    RepositoryIndexationRequested,
)
from issue_solver.events.event_store import EventStore
from issue_solver.events.serializable_records import serialize
from issue_solver.git_operations.git_helper import GitHelper, GitSettings
from issue_solver.webapi.dependencies import get_event_store, get_logger, get_clock
from issue_solver.webapi.payloads import ConnectRepositoryRequest

router = APIRouter(prefix="/repositories", tags=["repositories"])


async def validate_repository_access(url: str, access_token: str, logger: logging.Logger) -> None:
    """
    Validate that the repository can be accessed with the provided URL and token.
    
    Args:
        url: Repository URL
        access_token: Access token for the repository
        logger: Logger instance
        
    Raises:
        HTTPException: If the repository cannot be accessed
    """
    logger.info(f"Validating repository access: {url}")
    
    # Create a temporary directory for validation
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        try:
            # Try a minimal git operation to validate access
            git_helper = GitHelper.of(
                GitSettings(repository_url=url, access_token=access_token)
            )
            
            # Use git ls-remote which doesn't clone the repo but checks access
            repo = git.cmd.Git()
            auth_url = git_helper._inject_access_token(url)
            repo.execute(['git', 'ls-remote', '--quiet', auth_url])
            
            logger.info(f"Successfully validated repository access: {url}")
        except git.exc.GitCommandError as e:
            logger.error(f"Git command error: {str(e)}")
            
            # Determine error type based on error message
            error_message = str(e)
            if "Authentication failed" in error_message or "401" in error_message:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication failed. Please check your access token."
                )
            elif "not found" in error_message or "404" in error_message:
                raise HTTPException(
                    status_code=404,
                    detail="Repository not found. Please check the URL."
                )
            elif "could not resolve host" in error_message or "unable to access" in error_message:
                raise HTTPException(
                    status_code=502,
                    detail="Could not access the repository. Please check the URL and your internet connection."
                )
            elif "Permission denied" in error_message or "403" in error_message:
                raise HTTPException(
                    status_code=403,
                    detail="Permission denied. Check your access rights to this repository."
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to access repository: {error_message}"
                )
        except Exception as e:
            logger.error(f"Unexpected error validating repository: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error validating repository: {str(e)}"
            )


@router.post("/", status_code=201)
async def connect_repository(
    connect_repository_request: ConnectRepositoryRequest,
    event_store: Annotated[EventStore, Depends(get_event_store)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(lambda: get_logger("issue_solver.webapi.routers.repository.connect")),
    ],
    clock: Annotated[Clock, Depends(get_clock)],
) -> dict[str, str]:
    """Connect to a code repository."""
    # Validate repository access before proceeding
    await validate_repository_access(
        connect_repository_request.url, 
        connect_repository_request.access_token,
        logger
    )
    
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
