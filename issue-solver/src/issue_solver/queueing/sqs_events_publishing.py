import logging
import os
from typing import Any, Type

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException

from issue_solver.events.domain import AnyDomainEvent, T
from issue_solver.events.event_store import EventStore
from issue_solver.events.serializable_records import serialize


def publish(
    event: AnyDomainEvent,
    logger: logging.Logger | logging.LoggerAdapter,
    queue_url: str | None = None,
) -> None:
    """Publish a CodeRepositoryConnected event to SQS."""
    try:
        logger.info(f"Publishing event for process ID: {event.process_id}")
        sqs_client = boto3.client(
            "sqs", region_name=os.environ.get("AWS_REGION", "eu-west-3")
        )

        queue_url = queue_url or os.environ.get("PROCESS_QUEUE_URL")
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


class SQSQueueingEventStore(EventStore):
    def __init__(self, event_store: EventStore, queue_url: str) -> None:
        self.queue_url = queue_url
        self._event_store = event_store

    async def append(self, process_id: str, *events: AnyDomainEvent) -> None:
        await self._event_store.append(process_id, *events)
        for event in events:
            publish(event, logging.getLogger(__name__), self.queue_url)

    async def get(self, process_id: str) -> list[AnyDomainEvent]:
        return await self._event_store.get(process_id)

    async def find(self, criteria: dict[str, Any], event_type: Type[T]) -> list[T]:
        return await self._event_store.find(criteria, event_type)
