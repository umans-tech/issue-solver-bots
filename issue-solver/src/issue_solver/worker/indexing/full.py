import json
import os
from pathlib import Path

from issue_solver.events.domain import (
    CodeRepositoryConnected,
    CodeRepositoryIndexed,
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
from issue_solver.worker.indexing.delta import MICROVM_LIFETIME_IN_SECONDS


async def index_codebase(
    message: CodeRepositoryConnected, dependencies: Dependencies
) -> None:
    # Extract message data
    url = message.url
    access_token = message.access_token
    if not access_token:
        logger.error("No access token found for repository indexing")
        return
    user_id = message.user_id
    process_id = message.process_id
    knowledge_base_id = message.knowledge_base_id
    logger.info(
        f"Processing repository: {url} for user: {user_id}, process: {process_id}"
    )
    to_path = Path(f"/tmp/repo/{process_id}")

    try:
        git_helper_factory = (
            dependencies.git_helper_factory or _default_git_helper_factory
        )
        git_helper = git_helper_factory(
            GitSettings(repository_url=url, access_token=access_token),
            get_validation_service(),
        )
        code_version = git_helper.clone_repository(to_path)
        logger.info(f"Successfully cloned repository: {url}")

        if _should_offload_full_indexing_to_microvm(dependencies):
            _offload_full_indexing_to_microvm(
                access_token=access_token,
                dependencies=dependencies,
                knowledge_base_id=knowledge_base_id,
                process_id=process_id,
                repo_url=url,
            )
            return

        if knowledge_base_id:
            logger.info(
                f"Uploading repository files to vector store: {knowledge_base_id}"
            )
            repository_indexer = (
                dependencies.repository_indexer or OpenAIVectorStoreRepositoryIndexer()
            )
            stats = repository_indexer.upload_full_repository(
                repo_path=to_path, vector_store_id=knowledge_base_id
            )
            logger.info(f"Vector store upload stats: {json.dumps(stats)}")
            await dependencies.event_store.append(
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
        await dependencies.event_store.append(
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
        await dependencies.event_store.append(
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


def _should_offload_full_indexing_to_microvm(dependencies: Dependencies) -> bool:
    return (
        dependencies.is_dev_environment_service_enabled
        and dependencies.microvm_client is not None
    )


def _offload_full_indexing_to_microvm(
    access_token: str,
    dependencies: Dependencies,
    knowledge_base_id: str,
    process_id: str,
    repo_url: str,
) -> None:
    client = dependencies.microvm_client
    if client is None:
        logger.error("MicroVM client not available for full indexing offload")
        return

    snapshot = get_snapshot(client, metadata={"type": "base"})
    if not snapshot:
        logger.error("No base snapshot available for MicroVM indexing")
        raise RuntimeError("base_snapshot_missing")

    instance = client.instances.start(
        snapshot_id=snapshot.id, ttl_seconds=MICROVM_LIFETIME_IN_SECONDS
    )
    env_script = IndexRepositoryCommandSettings(
        repo_url=repo_url,
        access_token=access_token,
        knowledge_base_id=knowledge_base_id,
        process_id=process_id,
        repo_path=Path(f"/tmp/repo/{process_id}"),
        webhook_base_url=os.environ.get("WEBHOOK_BASE_URL"),
        process_queue_url=None,
    ).to_env_script()
    env_script = _append_openai_env(env_script)
    cmd = run_as_umans_with_env(env_script, "cudu index-repository", background=True)
    exec_response = instance.exec(cmd)
    logger.info(
        f"MicroVM full indexing offload started "
        f"instance_id={instance.id} exit_code={exec_response.exit_code} "
        f"stdout={exec_response.stdout!r} stderr={exec_response.stderr!r}"
    )


def _default_git_helper_factory(
    settings: GitSettings, validation_service=None
) -> GitHelper:
    return GitHelper.of(settings, validation_service=validation_service)


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
