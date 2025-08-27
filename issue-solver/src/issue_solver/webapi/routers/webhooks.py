import json
import logging
from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends
from redis import Redis

from issue_solver.events.serializable_records import ProcessTimelineEventRecords
from issue_solver.queueing.sqs_events_publishing import publish
from issue_solver.streaming.streaming_agent_message_store import get_messages_channel
from issue_solver.webapi.dependencies import get_redis_client, get_logger
from issue_solver.webapi.payloads import AgentMessageNotification

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/events", status_code=200)
async def notify_event_received(event: ProcessTimelineEventRecords) -> None:
    """Endpoint to receive webhook events."""
    domain_event = event.to_domain_event()
    publish(domain_event, logger=logging.getLogger(__name__))


@router.post("/messages", status_code=200)
async def notify_message_received(
    agent_message_record: AgentMessageNotification,
    redis_client: Annotated[Redis, Depends(get_redis_client)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(
            lambda: get_logger(
                "issue_solver.webapi.routers.webhooks.notify_message_received"
            )
        ),
    ],
) -> None:
    """Endpoint to receive webhook messages."""

    agent_message = agent_message_record.agent_message
    process_id = agent_message_record.process_id

    messages_channel = get_messages_channel(process_id)
    logger.info(f"Publishing message to channel {messages_channel}: {agent_message}")
    redis_client.publish(messages_channel, json.dumps(asdict(agent_message)))
