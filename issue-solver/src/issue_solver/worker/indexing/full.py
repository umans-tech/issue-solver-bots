import json
from pathlib import Path

from openai import OpenAI

from issue_solver.database.init_event_store import (
    extract_direct_database_url,
)
from issue_solver.events.domain import (
    CodeRepositoryConnected,
    CodeRepositoryIndexed,
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
    upload_repository_files_to_vector_store,
)


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

    try:
        # Use the validation service from dependencies
        git_helper = GitHelper.of(
            GitSettings(repository_url=url, access_token=access_token),
            validation_service=get_validation_service(),
        )
        code_version = git_helper.clone_repository(to_path)
        logger.info(f"Successfully cloned repository: {url}")

        # Upload repository files to vector store if knowledge_base_id is provided
        if knowledge_base_id:
            logger.info(
                f"Uploading repository files to vector store: {knowledge_base_id}"
            )
            client = OpenAI()
            stats = upload_repository_files_to_vector_store(
                repo_path=to_path, vector_store_id=knowledge_base_id, client=client
            )
            logger.info(f"Vector store upload stats: {json.dumps(stats)}")
            event_store = await init_event_store(
                database_url=extract_direct_database_url()
            )
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
            logger.warning(
                "No knowledge_base_id provided, skipping vector store upload"
            )
        logger.info(f"Successfully processed repository: {url}")

    except GitValidationError as e:
        logger.error(f"Git validation error: {e.message}")

        # Record the failure event
        event_store = await init_event_store(database_url=extract_direct_database_url())
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
        logger.error(f"Unexpected error processing repository: {str(e)}")

        # Record the failure event with a generic error
        event_store = await init_event_store(database_url=extract_direct_database_url())
        await event_store.append(
            process_id,
            CodeRepositoryIntegrationFailed(
                url=url,
                error_type="unexpected_error",
                error_message=f"An unexpected error occurred: {str(e)}",
                knowledge_base_id=knowledge_base_id,
                process_id=process_id,
                occurred_at=get_clock().now(),
            ),
        )
