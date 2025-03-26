import json
import logging
from pathlib import Path

from openai import OpenAI

from issue_solver.events.domain import (
    AnyDomainEvent,
    CodeRepositoryConnected,
    CodeRepositoryIndexed,
)
from issue_solver.git_operations.git_helper import GitHelper, GitSettings
from issue_solver.webapi.dependencies import init_event_store, get_clock
from issue_solver.worker.vector_store_helper import (
    upload_repository_files_to_vector_store,
)

logger = logging.getLogger()


async def process_event_message(message: AnyDomainEvent) -> None:
    """
    Process a repository connection message.

    Args:
        message: The SQS message containing repository information
    """
    try:
        match message:
            case CodeRepositoryConnected():
                await index_codebase(message)
            case CodeRepositoryIndexed():
                logger.info("Skipping already processed repository")

    except Exception as e:
        logger.error(f"Error processing repository message: {str(e)}")
        raise


async def index_codebase(message: CodeRepositoryConnected) -> None:
    # Extract message data
    url = message.url
    access_token = message.access_token
    user_id = message.user_id
    process_id = message.process_id
    knowledge_base_id = message.knowledge_base_id
    logger.info(
        f"Processing repository: {url} for user: {user_id}, process: {process_id}"
    )
    to_path = Path(f"/tmp/repo/{process_id}")
    code_version = GitHelper.of(
        GitSettings(repository_url=url, access_token=access_token)
    ).clone_repository(to_path)
    logger.info(f"Successfully cloned repository: {url}")
    # Upload repository files to vector store if knowledge_base_id is provided
    if knowledge_base_id:
        logger.info(f"Uploading repository files to vector store: {knowledge_base_id}")
        client = OpenAI()
        stats = upload_repository_files_to_vector_store(
            repo_path=to_path, vector_store_id=knowledge_base_id, client=client
        )
        logger.info(f"Vector store upload stats: {json.dumps(stats)}")
        event_store = await init_event_store()
        await event_store.append(
            process_id,
            CodeRepositoryIndexed(
                branch=code_version.branch,
                commit_sha=code_version.commit_sha,
                stats=stats,
                knowledge_base_id=knowledge_base_id,
                process_id=process_id,
                occurred_at=get_clock().now(),
            ),
        )
    else:
        logger.warning("No knowledge_base_id provided, skipping vector store upload")
    logger.info(f"Successfully processed repository: {url}")
