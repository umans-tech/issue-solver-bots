import logging
import os

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException

from issue_solver.events.domain import AnyDomainEvent
from issue_solver.events.serializable_records import serialize


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
