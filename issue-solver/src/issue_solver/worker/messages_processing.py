import json
import logging
from pathlib import Path

from issue_solver.events.domain import (
    AnyDomainEvent,
    CodeRepositoryConnected,
    CodeRepositoryIndexed,
    RepositoryIndexationRequested,
    most_recent_event,
)
from issue_solver.git_operations.git_helper import GitHelper, GitSettings
from issue_solver.webapi.dependencies import get_clock, init_event_store
from issue_solver.worker.vector_store_helper import (
    upload_repository_files_to_vector_store,
    unindex_obsolete_files,
    index_new_files,
    get_obsolete_files_ids,
)
from openai import OpenAI

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
            case RepositoryIndexationRequested():
                await index_new_changes_codebase(message)
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


async def index_new_changes_codebase(message: RepositoryIndexationRequested) -> None:
    # Extract message data
    process_id = message.process_id
    knowledge_base_id = message.knowledge_base_id
    logger.info(
        f"Processing repository indexation for process: {process_id}, knowledge_base_id: {knowledge_base_id}"
    )
    event_store = await init_event_store()
    events = await event_store.get(process_id)
    last_indexed_event = most_recent_event(events, CodeRepositoryIndexed)
    code_repository_connected = most_recent_event(events, CodeRepositoryConnected)
    if last_indexed_event is None or code_repository_connected is None:
        logger.warning("Missing events for process, skipping indexation")
        return
    last_indexed_commit_sha = last_indexed_event.commit_sha
    access_token = code_repository_connected.access_token
    url = code_repository_connected.url
    git_helper = GitHelper.of(
        GitSettings(repository_url=url, access_token=access_token)
    )
    to_path = Path(f"/tmp/repo/{process_id}")
    if not to_path.exists():
        logger.info("Cloning repository")
        code_version = git_helper.clone_repository(to_path, depth=None)
    else:
        logger.info("Pulling repository")
        code_version = git_helper.pull_repository(to_path)

    files_to_index = git_helper.get_changed_files_commit(
        to_path, last_indexed_commit_sha
    )

    if not files_to_index:
        logger.info("No new commits found, skipping indexation")
        return
    logger.info(f"Indexing commit: {last_indexed_commit_sha}")
    logger.info(f"Indexing files: {files_to_index}")

    client = OpenAI()

    obsolete_files = get_obsolete_files_ids(
        files_to_index.get_paths_of_all_obsolete_files(), client, knowledge_base_id
    )
    logger.info(f"Obsolete files stats: {json.dumps(obsolete_files.stats)}")

    new_indexed_files_stats = index_new_files(
        files_to_index.get_paths_of_all_new_files(), client, knowledge_base_id
    )
    logger.info(f"Vector store upload stats: {json.dumps(new_indexed_files_stats)}")

    unindexed_files_stats = unindex_obsolete_files(
        obsolete_files.file_ids_path, client, knowledge_base_id
    )
    logger.info(f"Vector store unindexing stats: {json.dumps(unindexed_files_stats)}")

    await event_store.append(
        process_id,
        CodeRepositoryIndexed(
            branch=code_version.branch,
            commit_sha=code_version.commit_sha,
            stats={
                "unindexed_files": unindexed_files_stats,
                "new_indexed_files": new_indexed_files_stats,
            },
            knowledge_base_id=knowledge_base_id,
            process_id=process_id,
            occurred_at=get_clock().now(),
        ),
    )
