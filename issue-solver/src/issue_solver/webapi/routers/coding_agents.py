import logging
import uuid
from typing import Annotated
import os
import boto3
from botocore.exceptions import ClientError

from fastapi import APIRouter, Depends, HTTPException
from issue_solver.clock import Clock
from issue_solver.events.domain import CodingAgentRequested, AnyDomainEvent
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
from issue_solver.webapi.payloads import CodingAgentRequest
from issue_solver.webapi.routers.repository import publish


router = APIRouter(prefix="/coding_agents", tags=["coding_agents"])

@router.post("/{knowledge_base_id}/implement", status_code=201)
async def implement_issue(
    knowledge_base_id: str,
    coding_agent_request: CodingAgentRequest,
    event_store: Annotated[EventStore, Depends(get_event_store)],
    logger: Annotated[logging.Logger, Depends(get_logger("issue_solver.webapi.routers.resolutions.implement"))],
    clock: Annotated[Clock, Depends(get_clock)],
    validation_service: Annotated[GitValidationService, Depends(get_validation_service)],
) -> dict[str, str]:
    """Implement the issue using the coding agent."""
    process_id = str(uuid.uuid4())
    logger.info(f"Creating new coding agent implementation with process ID: {process_id}")
    
    event = CodingAgentRequested(
        occurred_at=clock.now(),
        knowledge_base_id=knowledge_base_id,
        user_id=coding_agent_request.user_id,
        task_description=coding_agent_request.task_description,
        branch_name=coding_agent_request.branch_name,
        pr_title=coding_agent_request.pr_title,
        process_id=process_id,
    )
    
    await event_store.append(process_id, event)
    
    publish_logger = get_logger("issue_solver.webapi.routers.coding_agents.publish")
    publish_coding_agent_event(event, publish_logger)
    
    logger.info(f"Coding agent implementation created successfully with process ID: {process_id}")
    
    return {
        "process_id": event.process_id,
        "knowledge_base_id": event.knowledge_base_id,
        "pr_title": event.pr_title,
        "task_description": event.task_description,
    }

def publish_coding_agent_event(
    event: AnyDomainEvent, logger: logging.Logger | logging.LoggerAdapter
) -> None:
    """Publish a CodingAgentRequested event to SQS."""
    try:
        logger.info(f"Publishing coding agent event for process ID: {event.process_id}")
        sqs_client = boto3.client(
            "sqs", region_name=os.environ.get("AWS_REGION", "eu-west-3")
        )

        queue_url = os.environ.get("CODING_AGENT_QUEUE_URL")
        if not queue_url:
            raise ValueError("CODING_AGENT_QUEUE_URL environment variable not set")

        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=serialize(event).model_dump_json(),
        )

        logger.info(
            f"Published coding agent event ID {event.process_id} successfully with message ID {response['MessageId']}"
        )

    except (ClientError, ValueError) as e:
        logger.error(f"Failed to publish coding agent event {event.process_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to send message to SQS: {str(e)}"
        )
