"""
Lambda handler for processing repository connection messages from SQS.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict

import boto3
from morphcloud.api import MorphCloudClient

from issue_solver.agents.claude_code_agent import ClaudeCodeAgent
from issue_solver.agents.claude_code_docs_agent import ClaudeCodeDocsAgent
from issue_solver.database.init_event_store import extract_direct_database_url
from issue_solver.events.domain import AnyDomainEvent
from issue_solver.events.serializable_records import deserialize
from issue_solver.factories import init_event_store
from issue_solver.git_operations.git_helper import GitClient
from issue_solver.webapi.dependencies import (
    get_clock,
    init_agent_message_store,
)
from issue_solver.worker.documenting.s3_knowledge_repository import (
    S3KnowledgeRepository,
)
from issue_solver.worker.indexing.timeout_recovery import recover_timed_out_indexing
from issue_solver.worker.messages_processing import (
    process_event_message,
)
from issue_solver.worker.dependencies import Dependencies
from issue_solver.worker.logging_config import logger

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

        if event.get("source") == "scheduled.repository.indexing.timeout-recovery":
            logger.info("Running scheduled recovery check")
            asyncio.run(load_dependencies_and_recover_timed_out_indexing())
            return {"statusCode": 200, "body": "Recovery check complete"}

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
                asyncio.run(load_dependencies_and_process_event_message(event_record))
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in message body: {message_body}")
                continue

        return {"statusCode": 200, "body": "Processing complete"}

    except Exception as e:
        logger.error(f"Error in handler: {str(e)}")
        return {"statusCode": 500, "body": f"Error: {str(e)}"}


async def load_dependencies_and_process_event_message(
    event_record: AnyDomainEvent,
) -> None:
    dependencies = await load_dependencies()
    await process_event_message(
        event_record,
        dependencies,
    )


async def load_dependencies_and_recover_timed_out_indexing():
    dependencies = await load_dependencies()
    await recover_timed_out_indexing(dependencies)


async def load_dependencies() -> Dependencies:
    event_store = await init_event_store(
        database_url=extract_direct_database_url(),
        queue_url=os.getenv("PROCESS_QUEUE_URL"),
    )
    agent_message_store = await init_agent_message_store()
    is_dev_environment_service_enabled = bool(
        os.environ["DEV_ENVIRONMENT_SERVICE_ENABLED"]
    )
    dependencies = Dependencies(
        event_store=event_store,
        git_client=GitClient(),
        coding_agent=ClaudeCodeAgent(
            api_key=os.environ["ANTHROPIC_API_KEY"], agent_messages=agent_message_store
        ),
        knowledge_repository=S3KnowledgeRepository(
            s3_client=boto3.client("s3"),
            bucket_name=os.environ["KNOWLEDGE_BUCKET_NAME"],
        ),
        clock=get_clock(),
        microvm_client=MorphCloudClient() if "MORPH_API_KEY" in os.environ else None,
        is_dev_environment_service_enabled=is_dev_environment_service_enabled,
        docs_agent=ClaudeCodeDocsAgent(
            api_key=os.environ["ANTHROPIC_API_KEY"], agent_messages=agent_message_store
        ),
    )
    return dependencies
