import json
from pathlib import Path

from openai import OpenAI

from issue_solver.database.init_event_store import extract_direct_database_url
from issue_solver.events.code_repo_integration import get_access_token
from issue_solver.events.domain import (
    RepositoryIndexationRequested,
    most_recent_event,
    CodeRepositoryIndexed,
    CodeRepositoryConnected,
    CodeRepositoryIntegrationFailed,
)
from issue_solver.factories import init_event_store
from issue_solver.git_operations.git_helper import (
    GitHelper,
    GitSettings,
    GitValidationError,
)
from issue_solver.webapi.dependencies import (
    get_validation_service,
    get_clock,
)
from issue_solver.worker.logging_config import logger
from issue_solver.worker.vector_store_helper import (
    get_obsolete_files_ids,
    index_new_files,
    unindex_obsolete_files,
)


async def index_new_changes_codebase(message: RepositoryIndexationRequested) -> None:
    # Extract message data
    process_id = message.process_id
    knowledge_base_id = message.knowledge_base_id
    logger.info(
        f"Processing repository indexation for process: {process_id}, knowledge_base_id: {knowledge_base_id}"
    )
    event_store = await init_event_store(database_url=extract_direct_database_url())
    events = await event_store.get(process_id)
    last_indexed_event = most_recent_event(events, CodeRepositoryIndexed)
    code_repository_connected = most_recent_event(events, CodeRepositoryConnected)
    if last_indexed_event is None or code_repository_connected is None:
        logger.warning("Missing events for process, skipping indexation")
        return
    last_indexed_commit_sha = last_indexed_event.commit_sha
    access_token = await get_access_token(
        event_store, code_repository_connected.process_id
    )
    url = code_repository_connected.url

    try:
        # Use the validation service from dependencies
        git_helper = GitHelper.of(
            GitSettings(repository_url=url, access_token=access_token),
            validation_service=get_validation_service(),
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
            files_to_index.get_paths_of_all_obsolete_files(),
            client,
            knowledge_base_id,
        )
        logger.info(f"Obsolete files stats: {json.dumps(obsolete_files.stats)}")

        new_indexed_files_stats = index_new_files(
            files_to_index.get_paths_of_all_new_files(), client, knowledge_base_id
        )
        logger.info(f"Vector store upload stats: {json.dumps(new_indexed_files_stats)}")

        unindexed_files_stats = unindex_obsolete_files(
            obsolete_files.file_ids_path, client, knowledge_base_id
        )
        logger.info(f"Unindexed files stats: {json.dumps(unindexed_files_stats)}")

        # Store the updated repository indexation event
        await event_store.append(
            process_id,
            CodeRepositoryIndexed(
                branch=code_version.branch,
                commit_sha=code_version.commit_sha,
                stats={
                    "new_indexed_files": new_indexed_files_stats,
                    "obsolete_files": obsolete_files.stats,
                    "unindexed_files": unindexed_files_stats,
                },
                knowledge_base_id=knowledge_base_id,
                process_id=process_id,
                occurred_at=get_clock().now(),
            ),
        )
        logger.info(f"Successfully reindexed repository: {url}")

    except GitValidationError as e:
        logger.error(f"Git validation error: {e.message}")

        # Use the error information from the GitValidationError
        await event_store.append(
            process_id,
            CodeRepositoryIntegrationFailed(
                url=url,
                error_type=e.error_type,
                error_message=e.message,
                knowledge_base_id=knowledge_base_id,
                process_id=process_id,
                occurred_at=get_clock().now(),
            ),
        )

    except Exception as e:
        logger.error(f"Unexpected error during reindexing: {str(e)}")

        # Record the failure event with a generic error
        await event_store.append(
            process_id,
            CodeRepositoryIntegrationFailed(
                url=url,
                error_type="unexpected_error",
                error_message=f"An unexpected error occurred during reindexing: {str(e)}",
                knowledge_base_id=knowledge_base_id,
                process_id=process_id,
                occurred_at=get_clock().now(),
            ),
        )
