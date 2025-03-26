"""
SQS worker for local development.

This script continuously polls the LocalStack SQS queue and triggers the
Lambda handler (from lambda_handler.py) with an event structure similar to what
AWS Lambda receives.
"""

import logging
import os
import time

import boto3
from issue_solver.worker.lambda_handler import handler

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Dummy context to simulate the Lambda execution context
class DummyContext:
    def __init__(self):
        self.function_name = "local_worker"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = (
            "arn:aws:lambda:local:000000000000:function:local_worker"
        )
        self.aws_request_id = "local-request-id"


def poll_sqs(process_queue_url: str) -> None:
    # Create an SQS client pointing to LocalStack
    sqs = boto3.client(
        "sqs",
        endpoint_url=os.environ.get("AWS_ENDPOINT_URL"),
        region_name=os.environ["AWS_REGION"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )

    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=process_queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,  # Enable long polling
            )
            messages = response.get("Messages", [])
            if messages:
                logger.info(f"Received {len(messages)} message(s) from SQS")
                # Build an event object with all records
                records = []
                for msg in messages:
                    record = {
                        "messageId": msg.get("MessageId"),
                        "receiptHandle": msg.get("ReceiptHandle"),
                        "body": msg.get("Body"),
                        "attributes": msg.get("Attributes", {}),
                        "messageAttributes": msg.get("MessageAttributes", {}),
                    }
                    records.append(record)
                event = {"Records": records}
                context = DummyContext()
                # Call your production handler with the event and context
                result = handler(event, context)
                logger.info(f"Handler result: {result}")
                # Delete each processed message (This is what Lambda would do automatically)
                for msg in messages:
                    sqs.delete_message(
                        QueueUrl=process_queue_url,
                        ReceiptHandle=msg.get("ReceiptHandle"),
                    )
                    logger.info(f"Deleted message {msg.get('MessageId')}")
            else:
                logger.info("No messages received from SQS")
        except Exception as e:
            logger.exception(f"Error while polling SQS: {e}")
        # Small pause before polling again
        time.sleep(1)


if __name__ == "__main__":
    queue_url = os.environ["PROCESS_QUEUE_URL"]
    logger.info("Starting SQS worker poller...")
    poll_sqs(queue_url)
