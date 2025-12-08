import json
import os
from pathlib import Path

from issue_solver.events.code_repo_integration import get_access_token
from issue_solver.events.domain import (
    RepositoryIndexationRequested,
    most_recent_event,
    CodeRepositoryIndexed,
    CodeRepositoryConnected,
    CodeRepositoryIntegrationFailed,
)
from issue_solver.git_operations.git_helper import (
    GitHelper,
    GitSettings,
    GitValidationError,
)
from issue_solver.indexing.openai_repository_indexer import (
    OpenAIVectorStoreRepositoryIndexer,
)
from issue_solver.cli.index_repository_command import IndexRepositoryCommandSettings
from issue_solver.webapi.dependencies import (
    get_validation_service,
    get_clock,
)
from issue_solver.worker.logging_config import logger
from issue_solver.worker.dependencies import Dependencies
from issue_solver.env_setup.dev_environments_management import (
    run_as_umans_with_env,
    get_snapshot,
)

MICROVM_LIFETIME_IN_SECONDS = 90 * 60
DEFAULT_LARGE_DELTA_THRESHOLD = 200


async def index_new_changes_codebase(
    message: RepositoryIndexationRequested, dependencies: Dependencies
) -> None:
    # Extract message data
    process_id = message.process_id
    knowledge_base_id = message.knowledge_base_id
    logger.info(
        f"Processing repository indexation for process: {process_id}, knowledge_base_id: {knowledge_base_id}"
    )
    event_store = dependencies.event_store
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
    if not access_token:
        logger.error("No access token found for repository indexation")
        return

    try:
        git_helper_factory = (
            dependencies.git_helper_factory or _default_git_helper_factory
        )
        git_helper = git_helper_factory(
            GitSettings(repository_url=url, access_token=access_token),
            get_validation_service(),
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

        total_changed_files = len(files_to_index.get_paths_of_all_new_files()) + len(
            files_to_index.get_paths_of_all_obsolete_files()
        )
        if _delta_is_likely_slow_and_microvm_ready(total_changed_files, dependencies):
            _offload_delta_indexing_to_microvm(
                access_token=access_token,
                dependencies=dependencies,
                knowledge_base_id=knowledge_base_id,
                last_indexed_commit_sha=last_indexed_commit_sha,
                process_id=process_id,
                total_changed_files=total_changed_files,
                url=url,
            )
            return

        logger.info(f"Indexing commit: {last_indexed_commit_sha}")
        logger.info(f"Indexing files: {files_to_index}")

        repository_indexer = (
            dependencies.repository_indexer or OpenAIVectorStoreRepositoryIndexer()
        )
        stats = repository_indexer.apply_delta(
            repo_path=to_path,
            diff=files_to_index,
            vector_store_id=knowledge_base_id,
        )
        logger.info(f"Indexing stats: {json.dumps(stats)}")

        # Store the updated repository indexation event
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


def _delta_is_likely_slow_and_microvm_ready(
    total_changed_files: int, dependencies: Dependencies
) -> bool:
    return (
        dependencies.is_dev_environment_service_enabled
        and dependencies.microvm_client is not None
        and total_changed_files >= _microvm_offload_threshold()
    )


def _offload_delta_indexing_to_microvm(
    access_token: str | None,
    dependencies: Dependencies,
    knowledge_base_id: str,
    last_indexed_commit_sha: str,
    process_id: str,
    total_changed_files: int,
    url: str,
) -> None:
    logger.info(
        f"Large delta ({total_changed_files} files). Offloading indexing to MicroVM."
    )
    client = dependencies.microvm_client
    if client is None:
        logger.error("MicroVM client not available for offload")
        return

    snapshot = get_snapshot(client, metadata={"type": "base"})
    if not snapshot:
        logger.error("No base snapshot available for MicroVM indexing")
        raise RuntimeError("base_snapshot_missing")

    if access_token is None:
        logger.error("No access token found for repository indexation")
        return

    instance = client.instances.start(
        snapshot_id=snapshot.id, ttl_seconds=MICROVM_LIFETIME_IN_SECONDS
    )
    env_script = IndexRepositoryCommandSettings(
        repo_url=url,
        access_token=access_token,
        knowledge_base_id=knowledge_base_id,
        process_id=process_id,
        repo_path=Path(f"/tmp/repo/{process_id}"),
        from_commit_sha=last_indexed_commit_sha,
        webhook_base_url=os.environ.get("WEBHOOK_BASE_URL"),
        process_queue_url=None,
    ).to_env_script()
    env_script = _append_openai_env(env_script)
    cmd = run_as_umans_with_env(
        env_script,
        "cudu index-repository",
        background=True,
    )
    exec_response = instance.exec(cmd)
    logger.info(
        f"MicroVM delta offload started "
        f"instance_id={instance.id} exit_code={exec_response.exit_code} "
        f"stdout={exec_response.stdout!r} stderr={exec_response.stderr!r}"
    )


def _microvm_offload_threshold() -> int:
    env_value = os.environ.get("MICROVM_INDEXING_THRESHOLD")
    if env_value and env_value.isdigit():
        return int(env_value)
    return DEFAULT_LARGE_DELTA_THRESHOLD


def _append_openai_env(env_script: str) -> str:
    lines = [env_script.rstrip(), ""]
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    if api_key:
        lines.append(f"export OPENAI_API_KEY='{api_key}'")
    if base_url:
        lines.append(f"export OPENAI_BASE_URL='{base_url}'")
    if len(lines) == 2:  # nothing added
        return env_script
    return "\n".join(lines) + "\n"


def _default_git_helper_factory(
    settings: GitSettings, validation_service=None
) -> GitHelper:
    return GitHelper.of(settings, validation_service=validation_service)
