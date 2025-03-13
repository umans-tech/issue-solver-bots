"""
Lambda handler for processing repository connection messages from SQS.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

from issue_solver.git_operations.git_helper import GitHelper, GitSettings

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Add a stream handler that sends logs to stdout (which CloudWatch captures)
logging_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logging_handler.setFormatter(formatter)
logger.addHandler(logging_handler)

# Add a log at startup to verify logging is working
logger.info("Lambda function initialized")


def process_repository_message(message: Dict[str, Any]) -> None:
    """
    Process a repository connection message.

    Args:
        message: The SQS message containing repository information
    """
    try:
        # Extract message data
        url = message.get("url")
        access_token = message.get("access_token")
        user_id = message.get("user_id")
        process_id = message.get("process_id")

        logger.info(
            f"Processing repository: {url} for user: {user_id}, process: {process_id}"
        )

        to_path = Path(f"/tmp/repo/{process_id}")
        
        GitHelper.of(
            GitSettings(repository_url=url, access_token=access_token)
        ).clone_repository(to_path)

        logger.info(f"Successfully processed repository: {url}")

    except Exception as e:
        logger.error(f"Error processing repository message: {str(e)}")
        raise


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
                process_repository_message(message)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in message body: {message_body}")
                continue

        return {"statusCode": 200, "body": "Processing complete"}

    except Exception as e:
        logger.error(f"Error in handler: {str(e)}")
        return {"statusCode": 500, "body": f"Error: {str(e)}"}
