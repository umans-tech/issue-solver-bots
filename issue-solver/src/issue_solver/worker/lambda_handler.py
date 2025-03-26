"""
Lambda handler for processing repository connection messages from SQS.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict

from issue_solver.events.serializable_records import deserialize
from issue_solver.worker.messages_processing import logger, process_event_message

# Configure logging
logger.setLevel(logging.INFO)

# Add a stream handler that sends logs to stdout (which CloudWatch captures)
logging_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logging_handler.setFormatter(formatter)
logger.addHandler(logging_handler)

# Add a log at startup to verify logging is working
logger.info("Lambda function initialized")


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for processing SQS messages.

    Args:
        event: The Lambda event containing SQS messages
        context: The Lambda context

    Returns:
        A response indicating success or failure
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        # Process each record (message) from SQS
        for record in event.get("Records", []):
            # Extract the message body
            message_body = record.get("body")
            if not message_body:
                logger.warning("Empty message body received")
                continue

            # Parse the message body
            try:
                message = json.loads(message_body)
                event_record = deserialize(message["type"], message_body)
                asyncio.run(process_event_message(event_record))
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in message body: {message_body}")
                continue

        return {"statusCode": 200, "body": "Processing complete"}

    except Exception as e:
        logger.error(f"Error in handler: {str(e)}")
        return {"statusCode": 500, "body": f"Error: {str(e)}"}
