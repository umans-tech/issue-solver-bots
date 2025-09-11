import os
from pathlib import Path

from morphcloud.api import MorphCloudClient

from issue_solver.agents.issue_resolving_agent import (
    IssueResolvingAgent,
    ResolveIssueCommand,
)
from issue_solver.agents.supported_agents import SupportedAgent
from issue_solver.cli.prepare_command import PrepareCommandSettings
from issue_solver.cli.solve_command_settings import SolveCommandSettings
from issue_solver.clock import Clock
from issue_solver.env_setup.dev_environments_management import (
    get_snapshot,
    run_as_umans_with_env,
)
from issue_solver.events.code_repo_integration import (
    get_repo_credentials,
)
from issue_solver.events.domain import (
    IssueResolutionRequested,
    IssueResolutionFailed,
    IssueResolutionEnvironmentPrepared,
    IssueResolutionStarted,
    IssueResolutionCompleted,
    EnvironmentConfigurationProvided,
    most_recent_event,
)
from issue_solver.events.event_store import EventStore
from issue_solver.git_operations.git_helper import (
    GitClient,
    extract_git_clone_default_directory_name,
    GitSettings,
)
from issue_solver.models.supported_models import (
    SupportedAnthropicModel,
    LATEST_CLAUDE_4_VERSION,
    QualifiedAIModel,
)
from issue_solver.worker.logging_config import logger

MICROVM_LIFETIME_IN_SECONDS = 90 * 60


class Dependencies:
    def __init__(
        self,
        event_store: EventStore,
        git_client: GitClient,
        coding_agent: IssueResolvingAgent,
        clock: Clock,
        microvm_client: MorphCloudClient | None = None,
        is_dev_environment_service_enabled: bool = False,
    ):
        self._event_store = event_store
        self.git_client = git_client
        self.coding_agent = coding_agent
        self.clock = clock
        self.microvm_client = microvm_client
        self.is_dev_environment_service_enabled = is_dev_environment_service_enabled

    @property
    def event_store(self) -> EventStore:
        return self._event_store


async def resolve_issue(
    message: IssueResolutionRequested, dependencies: Dependencies
) -> None:
    event_store = dependencies.event_store
    knowledge_base_id = message.knowledge_base_id
    repo_credentials = await get_repo_credentials(event_store, knowledge_base_id)
    if not repo_credentials:
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
    url = repo_credentials.url
    access_token = repo_credentials.access_token
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

    dev_environment_configuration = await fetch_environment_configuration(
        event_store, knowledge_base_id
    )
    if (
        dev_environment_configuration
        and dependencies.is_dev_environment_service_enabled
        and message.needs_environment()
    ):
        microvm_client = dependencies.microvm_client
        environment_id = dev_environment_configuration.environment_id
        if microvm_client:
            snapshot = get_snapshot(
                microvm_client,
                {
                    "type": "dev",
                    "knowledge_base_id": knowledge_base_id,
                    "environment_id": environment_id,
                },
            )
            default_clone_path = Path(extract_git_clone_default_directory_name(url))
            if not snapshot:
                snapshot = get_snapshot(microvm_client, {"type": "base"})
                if snapshot:
                    prepare_body = PrepareCommandSettings(
                        process_id=process_id,
                        repo_path=default_clone_path,
                        url=url,
                        access_token=access_token,
                        issue=message.issue,  # see Note below
                        install_script=dev_environment_configuration.project_setup,
                    ).to_env_script()
                    cmd = run_as_umans_with_env(
                        prepare_body,
                        "cudu prepare",
                        dev_environment_configuration.global_setup,
                    )
                    snapshot = snapshot.exec(cmd)
                    snapshot.set_metadata(
                        {
                            "type": "dev",
                            "knowledge_base_id": knowledge_base_id,
                            "environment_id": environment_id,
                        }
                    )

            if snapshot:
                instance = microvm_client.instances.start(
                    snapshot_id=snapshot.id, ttl_seconds=MICROVM_LIFETIME_IN_SECONDS
                )
                await event_store.append(
                    process_id,
                    IssueResolutionEnvironmentPrepared(
                        process_id=process_id,
                        occurred_at=dependencies.clock.now(),
                        knowledge_base_id=knowledge_base_id,
                        environment_id=environment_id,
                        instance_id=instance.id,
                    ),
                )
                solve_command_settings = SolveCommandSettings(
                    process_id=process_id,
                    issue=message.issue,
                    agent=SupportedAgent.CLAUDE_CODE,
                    git=GitSettings(repository_url=url, access_token=access_token),
                    ai_model=SupportedAnthropicModel.CLAUDE_SONNET_4,
                    ai_model_version=LATEST_CLAUDE_4_VERSION,
                    repo_path=default_clone_path,
                    webhook_base_url=os.environ.get("WEBHOOK_BASE_URL"),
                    process_queue_url=None,
                    redis_url=None,
                )
                env_script = solve_command_settings.to_env_script()
                instance.wait_until_ready()
                solve_command_script = run_as_umans_with_env(env_script, "cudu solve")
                instance_exec_response = instance.exec(solve_command_script)
                print(f"Instance exec STDOUT: {instance_exec_response.stdout}")
                print(f"Instance exec STDERR: {instance_exec_response.stderr}")
                if instance_exec_response.exit_code != 0:
                    logger.error(
                        f"Instance execution failed with return code {instance_exec_response.exit_code}"
                    )
                    await event_store.append(
                        process_id,
                        IssueResolutionFailed(
                            process_id=process_id,
                            occurred_at=dependencies.clock.now(),
                            reason="instance_exec_failed",
                            error_message=instance_exec_response.stderr,
                        ),
                    )
    else:
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


async def fetch_environment_configuration(
    event_store: EventStore, knowledge_base_id: str
) -> EnvironmentConfigurationProvided | None:
    environments_configurations = await event_store.find(
        {"knowledge_base_id": knowledge_base_id}, EnvironmentConfigurationProvided
    )
    most_recent_environment_configuration = most_recent_event(
        environments_configurations, EnvironmentConfigurationProvided
    )
    return most_recent_environment_configuration
