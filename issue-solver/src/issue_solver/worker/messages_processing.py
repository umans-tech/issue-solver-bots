import json
import logging
from pathlib import Path

from openai import OpenAI

from issue_solver.agents.issue_resolving_agent import (
    IssueResolvingAgent,
    ResolveIssueCommand,
)
from issue_solver.clock import Clock
from issue_solver.events.domain import (
    AnyDomainEvent,
    CodeRepositoryConnected,
    CodeRepositoryIndexed,
    CodeRepositoryIntegrationFailed,
    RepositoryIndexationRequested,
    most_recent_event,
    IssueResolutionRequested,
    IssueResolutionStarted,
    IssueResolutionCompleted,
    IssueResolutionFailed,
)
from issue_solver.events.code_repo_integration import (
    get_access_token,
)
from issue_solver.events.event_store import EventStore
from issue_solver.git_operations.git_helper import (
    GitHelper,
    GitSettings,
    GitValidationError,
    GitClient,
)
from issue_solver.models.supported_models import (
    QualifiedAIModel,
    SupportedAnthropicModel,
    LATEST_CLAUDE_4_VERSION,
)
from issue_solver.webapi.dependencies import (
    get_clock,
    get_validation_service,
    init_event_store,
)
from issue_solver.worker.vector_store_helper import (
    get_obsolete_files_ids,
    index_new_files,
    unindex_obsolete_files,
    upload_repository_files_to_vector_store,
)

logger = logging.getLogger()


class Dependencies:
    def __init__(
        self,
        event_store: EventStore,
        git_client: GitClient,
        coding_agent: IssueResolvingAgent,
        clock: Clock,
    ):
        self._event_store = event_store
        self.git_client = git_client
        self.coding_agent = coding_agent
        self.clock = clock

    @property
    def event_store(self) -> EventStore:
        return self._event_store


async def resolve_issue(
    message: IssueResolutionRequested, dependencies: Dependencies
) -> None:
    event_store = dependencies.event_store
    knowledge_base_id = message.knowledge_base_id
    repo_events = await event_store.find(
        {"knowledge_base_id": knowledge_base_id}, CodeRepositoryConnected
    )
    if not repo_events:
        logger.error(f"Knowledge base ID {knowledge_base_id} not found in event store")
        await event_store.append(
            message.process_id,
            IssueResolutionFailed(
                process_id=message.process_id,
                occurred_at=message.occurred_at,
                reason="repo_not_found",
                error_message=f"Knowledge base ID {knowledge_base_id} not found.",
            ),
        )
        return
    code_repository_connected = repo_events[0]
    url = code_repository_connected.url
    access_token = await get_access_token(
        event_store, code_repository_connected.process_id
    )
    if not access_token:
        logger.error(f"No access token found for knowledge base ID {knowledge_base_id}")
        await event_store.append(
            message.process_id,
            IssueResolutionFailed(
                process_id=message.process_id,
                occurred_at=message.occurred_at,
                reason="no_access_token",
                error_message="No access token found for repository.",
            ),
        )
        return
    process_id = message.process_id
    repo_path = Path(f"/tmp/repo/{process_id}")
    try:
        dependencies.git_client.clone_repo_and_branch(
            process_id, repo_path, url, access_token, message.issue
        )
    except Exception as e:
        logger.error(f"Error cloning repository: {str(e)}")
        await event_store.append(
            message.process_id,
            IssueResolutionFailed(
                process_id=message.process_id,
                occurred_at=dependencies.clock.now(),
                reason="repo_cant_be_cloned",
                error_message=str(e),
            ),
        )
        return

    await dependencies.event_store.append(
        message.process_id,
        IssueResolutionStarted(
            process_id=message.process_id,
            occurred_at=dependencies.clock.now(),
        ),
    )

    # Run coding agent
    try:
        await dependencies.coding_agent.resolve_issue(
            ResolveIssueCommand(
                process_id=message.process_id,
                model=QualifiedAIModel(
                    ai_model=SupportedAnthropicModel.CLAUDE_SONNET_4,
                    version=LATEST_CLAUDE_4_VERSION,
                ),
                issue=message.issue,
                repo_path=repo_path,
            )
        )
    except Exception as e:
        logger.error(f"Error resolving issue: {str(e)}")
        await event_store.append(
            message.process_id,
            IssueResolutionFailed(
                process_id=message.process_id,
                occurred_at=dependencies.clock.now(),
                reason="coding_agent_failed",
                error_message=str(e),
            ),
        )
        return

    try:
        dependencies.git_client.commit_and_push(
            issue_info=message.issue,
            repo_path=repo_path,
            url=url,
            access_token=access_token,
        )
    except Exception as e:
        logger.error(f"Error committing changes: {str(e)}")
        await event_store.append(
            message.process_id,
            IssueResolutionFailed(
                process_id=message.process_id,
                occurred_at=dependencies.clock.now(),
                reason="failed_to_push_changes",
                error_message=str(e),
            ),
        )
        return
    # Submit PR
    try:
        pr_reference = dependencies.git_client.submit_pull_request(
            repo_path=repo_path,
            title=message.issue.title
            or f"automatic issue resolution {message.process_id}",
            body=message.issue.description,
            access_token=access_token,
            url=url,
        )
    except Exception as e:
        logger.error(f"Error creating pull request: {str(e)}")
        await event_store.append(
            message.process_id,
            IssueResolutionFailed(
                process_id=message.process_id,
                occurred_at=dependencies.clock.now(),
                reason="failed_to_submit_pr",
                error_message=str(e),
            ),
        )
        return

    await dependencies.event_store.append(
        message.process_id,
        IssueResolutionCompleted(
            process_id=message.process_id,
            occurred_at=dependencies.clock.now(),
            pr_url=pr_reference.url,
            pr_number=pr_reference.number,
        ),
    )


async def process_event_message(
    message: AnyDomainEvent, dependencies: Dependencies
) -> None:
    try:
        match message:
            case CodeRepositoryConnected():
                await index_codebase(message)
            case CodeRepositoryIndexed():
                logger.info("Skipping already processed repository")
            case RepositoryIndexationRequested():
                await index_new_changes_codebase(message)
            case IssueResolutionRequested():
                await resolve_issue(message, dependencies)
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
            logger.warning(
                "No knowledge_base_id provided, skipping vector store upload"
            )
        logger.info(f"Successfully processed repository: {url}")

    except GitValidationError as e:
        logger.error(f"Git validation error: {e.message}")

        # Record the failure event
        event_store = await init_event_store()
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
        event_store = await init_event_store()
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
