import os
from datetime import datetime
from unittest.mock import Mock, AsyncMock, call

import pytest
from morphcloud.api import (
    MorphCloudClient,
    Instance,
    ResourceSpec,
    Snapshot,
    SnapshotStatus,
    SnapshotRefs,
    InstanceExecResponse,
)
from tests.controllable_clock import ControllableClock

from issue_solver.agents.issue_resolving_agent import IssueResolvingAgent
from issue_solver.env_setup.dev_environments_management import (
    ExecutionEnvironmentPreference,
)
from issue_solver.events.domain import (
    IssueResolutionStarted,
    IssueResolutionRequested,
    IssueResolutionCompleted,
    IssueResolutionFailed,
    CodeRepositoryConnected,
    EnvironmentConfigurationProvided,
    IssueResolutionEnvironmentPrepared,
)
from issue_solver.git_operations.git_helper import (
    GitClient,
    PullRequestReference,
)
from issue_solver.issues.issue import IssueInfo
from issue_solver.worker.messages_processing import process_event_message
from issue_solver.worker.solving.process_issue_resolution_request import Dependencies


@pytest.mark.asyncio
async def test_given_issue_resolution_request_start_resolution(
    event_store, time_under_control: ControllableClock
):
    # Given
    time_under_control.set_from_iso_format("2025-05-13T10:38:49")
    indexation_process_id = "indexation_process_id"
    await event_store.append(
        indexation_process_id,
        CodeRepositoryConnected(
            url="test-url",
            access_token="test-access-token",
            user_id="test-user-id",
            space_id="test-space-id",
            occurred_at=datetime.fromisoformat("2025-05-13T10:35:00"),
            knowledge_base_id="test-knowledge-base-id",
            process_id=indexation_process_id,
        ),
    )
    process_id = "test-process-id"
    issue_resolution_requested_event = IssueResolutionRequested(
        occurred_at=datetime.fromisoformat("2025-05-13T10:36:12"),
        knowledge_base_id="test-knowledge-base-id",
        process_id=process_id,
        issue=IssueInfo(description="test issue"),
    )

    coding_agent = AsyncMock()
    git_client = Mock()
    git_client.submit_pull_request.return_value = PullRequestReference(
        url="http://gitlab.com/test-repo/pull/54",
        number=54,
    )

    # When
    await process_event_message(
        issue_resolution_requested_event,
        dependencies=Dependencies(
            event_store, git_client, coding_agent, time_under_control
        ),
    )
    # Then
    produced_events = await event_store.get(process_id)
    assert (
        IssueResolutionStarted(
            process_id=process_id,
            occurred_at=time_under_control.now(),
        )
        in produced_events
    )

    assert (
        IssueResolutionCompleted(
            process_id=process_id,
            occurred_at=time_under_control.now(),
            pr_url="http://gitlab.com/test-repo/pull/54",
            pr_number=54,
        )
        in produced_events
    )


@pytest.mark.asyncio
async def test_resolve_issue_should_fail_when_repo_cant_find_knowledge_base(
    event_store, time_under_control: ControllableClock
):
    # Given
    time_under_control.set_from_iso_format("2025-01-01T00:00:00")
    process_id = "test-process-id"
    unknown_knowledge_base_id = "unknown_knowledge_base_id"
    issue_resolution_requested_event = IssueResolutionRequested(
        occurred_at=time_under_control.now(),
        knowledge_base_id=unknown_knowledge_base_id,
        process_id=process_id,
        issue=IssueInfo(description="test issue"),
    )

    # When
    await process_event_message(
        issue_resolution_requested_event,
        dependencies=Dependencies(event_store, Mock(), AsyncMock(), time_under_control),
    )
    # Then
    produced_events = await event_store.get(process_id)

    assert (
        IssueResolutionFailed(
            process_id="test-process-id",
            occurred_at=time_under_control.now(),
            reason="repo_not_found",
            error_message=f"Knowledge base ID {unknown_knowledge_base_id} not found.",
        )
        in produced_events
    )


@pytest.mark.asyncio
async def test_resolve_issue_should_fail_when_repo_cant_be_cloned(
    event_store, time_under_control: ControllableClock
):
    # Given
    time_under_control.set_from_iso_format("2025-01-01T00:00:00")
    repo_integration_process_id = "indexation_process_id"
    repo_url = "http://gitlab.com/test-repo.git"
    await event_store.append(
        repo_integration_process_id,
        CodeRepositoryConnected(
            url=repo_url,
            access_token="s3cretAcc3ssT0k3n",
            user_id="test-user-id",
            space_id="test-space-id",
            occurred_at=time_under_control.now(),
            knowledge_base_id="test-knowledge-base-id",
            process_id=repo_integration_process_id,
        ),
    )
    issue_resolution_process_id = "test-process-id"
    issue_resolution_requested_event = IssueResolutionRequested(
        occurred_at=time_under_control.now(),
        knowledge_base_id="test-knowledge-base-id",
        process_id=issue_resolution_process_id,
        issue=IssueInfo(description="test issue"),
    )
    git_helper = Mock()
    git_helper.clone_repo_and_branch = Mock(
        side_effect=Exception(
            f"Cannot clone repository {repo_url} because of some reason"
        )
    )

    # When
    await process_event_message(
        issue_resolution_requested_event,
        dependencies=Dependencies(
            event_store, git_helper, AsyncMock(), time_under_control
        ),
    )
    # Then
    produced_events = await event_store.get(issue_resolution_process_id)

    assert (
        IssueResolutionFailed(
            process_id="test-process-id",
            occurred_at=time_under_control.now(),
            reason="repo_cant_be_cloned",
            error_message=f"Cannot clone repository {repo_url} because of some reason",
        )
        in produced_events
    )


@pytest.mark.asyncio
async def test_resolve_issue_should_fail_when_coding_agent_fails(
    event_store, time_under_control: ControllableClock
):
    # Given
    time_under_control.set_from_iso_format("2025-01-01T00:00:00")
    repo_integration_process_id = "indexation_process_id"
    await event_store.append(
        repo_integration_process_id,
        CodeRepositoryConnected(
            url="http://gitlab.com/test-repo.git",
            access_token="s3cretAcc3ssT0k3n",
            user_id="test-user-id",
            space_id="test-space-id",
            occurred_at=time_under_control.now(),
            knowledge_base_id="test-knowledge-base-id",
            process_id=repo_integration_process_id,
        ),
    )
    issue_resolution_process_id = "test-process-id"
    issue_resolution_requested_event = IssueResolutionRequested(
        occurred_at=time_under_control.now(),
        knowledge_base_id="test-knowledge-base-id",
        process_id=issue_resolution_process_id,
        issue=IssueInfo(description="test issue"),
    )
    git_helper = Mock()
    coding_agent = AsyncMock(spec=IssueResolvingAgent)
    coding_agent.resolve_issue.side_effect = Exception(
        "Coding agent failed to generate a solution."
    )

    # When
    await process_event_message(
        issue_resolution_requested_event,
        dependencies=Dependencies(
            event_store, git_helper, coding_agent, time_under_control
        ),
    )
    # Then
    produced_events = await event_store.get(issue_resolution_process_id)

    assert (
        IssueResolutionFailed(
            process_id="test-process-id",
            occurred_at=time_under_control.now(),
            reason="coding_agent_failed",
            error_message="Coding agent failed to generate a solution.",
        )
        in produced_events
    )


@pytest.mark.asyncio
async def test_resolve_issue_should_fail_when_fail_to_push_changes(
    event_store, time_under_control: ControllableClock
):
    # Given
    time_under_control.set_from_iso_format("2025-01-01T00:00:00")
    repo_integration_process_id = "indexation_process_id"
    await event_store.append(
        repo_integration_process_id,
        CodeRepositoryConnected(
            url="http://gitlab.com/test-repo.git",
            access_token="s3cretAcc3ssT0k3n",
            user_id="test-user-id",
            space_id="test-space-id",
            occurred_at=time_under_control.now(),
            knowledge_base_id="test-knowledge-base-id",
            process_id=repo_integration_process_id,
        ),
    )
    issue_resolution_process_id = "test-process-id"
    issue_resolution_requested_event = IssueResolutionRequested(
        occurred_at=time_under_control.now(),
        knowledge_base_id="test-knowledge-base-id",
        process_id=issue_resolution_process_id,
        issue=IssueInfo(description="test issue"),
    )
    git_helper = Mock(spec=GitClient)
    error_message = "Failed to push changes because of missing write access to the repository with token"
    git_helper.commit_and_push.side_effect = Exception(error_message)
    coding_agent = AsyncMock(spec=IssueResolvingAgent)

    # When
    await process_event_message(
        issue_resolution_requested_event,
        dependencies=Dependencies(
            event_store, git_helper, coding_agent, time_under_control
        ),
    )
    # Then
    produced_events = await event_store.get(issue_resolution_process_id)

    assert (
        IssueResolutionFailed(
            process_id="test-process-id",
            occurred_at=time_under_control.now(),
            reason="failed_to_push_changes",
            error_message=error_message,
        )
        in produced_events
    )


@pytest.mark.asyncio
async def test_resolve_issue_should_fail_when_fail_to_submit_pr(
    event_store, time_under_control: ControllableClock
):
    # Given
    time_under_control.set_from_iso_format("2025-01-01T00:00:00")
    repo_integration_process_id = "indexation_process_id"
    await event_store.append(
        repo_integration_process_id,
        CodeRepositoryConnected(
            url="http://gitlab.com/test-repo.git",
            access_token="s3cretAcc3ssT0k3n",
            user_id="test-user-id",
            space_id="test-space-id",
            occurred_at=time_under_control.now(),
            knowledge_base_id="test-knowledge-base-id",
            process_id=repo_integration_process_id,
        ),
    )
    issue_resolution_process_id = "test-process-id"
    issue_resolution_requested_event = IssueResolutionRequested(
        occurred_at=time_under_control.now(),
        knowledge_base_id="test-knowledge-base-id",
        process_id=issue_resolution_process_id,
        issue=IssueInfo(description="test issue"),
    )
    git_helper = Mock(spec=GitClient)
    error_message = "Failed to create pull request because of missing write access to pull request with token"
    git_helper.submit_pull_request.side_effect = Exception(error_message)
    coding_agent = AsyncMock(spec=IssueResolvingAgent)

    # When
    await process_event_message(
        issue_resolution_requested_event,
        dependencies=Dependencies(
            event_store, git_helper, coding_agent, time_under_control
        ),
    )
    # Then
    produced_events = await event_store.get(issue_resolution_process_id)

    assert (
        IssueResolutionFailed(
            process_id="test-process-id",
            occurred_at=time_under_control.now(),
            reason="failed_to_submit_pr",
            error_message=error_message,
        )
        in produced_events
    )


@pytest.mark.asyncio
async def test_issue_resolution_should_never_use_vm_when_env_service_is_disabled(
    event_store, time_under_control: ControllableClock
):
    # Given
    time_under_control.set_from_iso_format("2025-01-01T00:00:00")
    repo_integration_process_id = "indexation_process_id"
    await event_store.append(
        repo_integration_process_id,
        CodeRepositoryConnected(
            url="http://gitlab.com/test-repo.git",
            access_token="s3cretAcc3ssT0k3n",
            user_id="test-user-id",
            space_id="test-space-id",
            occurred_at=time_under_control.now(),
            knowledge_base_id="test-knowledge-base-id",
            process_id=repo_integration_process_id,
        ),
    )
    environment_config_process_id = "env-config-process-id"
    environment_id = "bob-dev-environment-05"
    await event_store.append(
        "environment_config_process_id",
        EnvironmentConfigurationProvided(
            environment_id=environment_id,
            occurred_at=time_under_control.now(),
            knowledge_base_id="test-knowledge-base-id",
            project_setup="echo 'Hello, World!'",
            user_id="test-user-id",
            process_id=environment_config_process_id,
        ),
    )
    issue_resolution_process_id = "test-process-id"
    issue_resolution_requested_event = IssueResolutionRequested(
        occurred_at=time_under_control.now(),
        knowledge_base_id="test-knowledge-base-id",
        process_id=issue_resolution_process_id,
        issue=IssueInfo(title="issue title", description="test issue"),
    )
    git_helper = Mock(spec=GitClient)
    coding_agent = AsyncMock(spec=IssueResolvingAgent)
    microvm_client = Mock(spec=MorphCloudClient)
    pr_number = 69
    git_helper.submit_pull_request.return_value = PullRequestReference(
        url="http://gitlab.com/test-repo/pull/69",
        number=pr_number,
    )

    # When
    await process_event_message(
        issue_resolution_requested_event,
        dependencies=Dependencies(
            event_store,
            git_helper,
            coding_agent,
            time_under_control,
            microvm_client,
            is_dev_environment_service_enabled=False,
        ),
    )
    # Then

    microvm_client.snapshots.list.assert_not_called()
    microvm_client.instances.start.assert_not_called()
    produced_events = await event_store.get(issue_resolution_process_id)

    assert produced_events == [
        IssueResolutionStarted(
            process_id=issue_resolution_process_id,
            occurred_at=time_under_control.now(),
        ),
        IssueResolutionCompleted(
            process_id=issue_resolution_process_id,
            occurred_at=time_under_control.now(),
            pr_url="http://gitlab.com/test-repo/pull/69",
            pr_number=pr_number,
        ),
    ]


@pytest.mark.asyncio
async def test_issue_resolution_should_never_use_vm_when_no_env_required(
    event_store, time_under_control: ControllableClock
):
    # Given
    time_under_control.set_from_iso_format("2025-01-01T00:00:00")
    repo_integration_process_id = "indexation_process_id"
    await event_store.append(
        repo_integration_process_id,
        CodeRepositoryConnected(
            url="http://gitlab.com/test-repo.git",
            access_token="s3cretAcc3ssT0k3n",
            user_id="test-user-id",
            space_id="test-space-id",
            occurred_at=time_under_control.now(),
            knowledge_base_id="test-knowledge-base-id",
            process_id=repo_integration_process_id,
        ),
    )
    environment_config_process_id = "env-config-process-id"
    environment_id = "bob-dev-environment-05"
    await event_store.append(
        "environment_config_process_id",
        EnvironmentConfigurationProvided(
            environment_id=environment_id,
            occurred_at=time_under_control.now(),
            knowledge_base_id="test-knowledge-base-id",
            project_setup="echo 'Hello, World!'",
            user_id="test-user-id",
            process_id=environment_config_process_id,
        ),
    )
    issue_resolution_process_id = "test-process-id"
    issue_resolution_requested_event = IssueResolutionRequested(
        occurred_at=time_under_control.now(),
        knowledge_base_id="test-knowledge-base-id",
        process_id=issue_resolution_process_id,
        issue=IssueInfo(title="issue title", description="test issue"),
        execution_environment=ExecutionEnvironmentPreference.NO_ENV_REQUIRED,
    )
    git_helper = Mock(spec=GitClient)
    coding_agent = AsyncMock(spec=IssueResolvingAgent)
    microvm_client = Mock(spec=MorphCloudClient)
    pr_number = 69
    git_helper.submit_pull_request.return_value = PullRequestReference(
        url="http://gitlab.com/test-repo/pull/69",
        number=pr_number,
    )

    # When
    await process_event_message(
        issue_resolution_requested_event,
        dependencies=Dependencies(
            event_store,
            git_helper,
            coding_agent,
            time_under_control,
            microvm_client,
            is_dev_environment_service_enabled=True,
        ),
    )
    # Then

    microvm_client.snapshots.list.assert_not_called()
    microvm_client.instances.start.assert_not_called()
    produced_events = await event_store.get(issue_resolution_process_id)

    assert produced_events == [
        IssueResolutionStarted(
            process_id=issue_resolution_process_id,
            occurred_at=time_under_control.now(),
        ),
        IssueResolutionCompleted(
            process_id=issue_resolution_process_id,
            occurred_at=time_under_control.now(),
            pr_url="http://gitlab.com/test-repo/pull/69",
            pr_number=pr_number,
        ),
    ]


@pytest.mark.asyncio
async def test_issue_resolution_should_use_vm_when_env_config_script_is_provided(
    event_store, time_under_control: ControllableClock
):
    # Given
    time_under_control.set_from_iso_format("2025-01-01T00:00:00")
    repo_integration_process_id = "indexation_process_id"
    await event_store.append(
        repo_integration_process_id,
        CodeRepositoryConnected(
            url="http://gitlab.com/test-repo.git",
            access_token="s3cretAcc3ssT0k3n",
            user_id="test-user-id",
            space_id="test-space-id",
            occurred_at=time_under_control.now(),
            knowledge_base_id="test-knowledge-base-id",
            process_id=repo_integration_process_id,
        ),
    )
    environment_config_process_id = "env-config-process-id"
    environment_id = "bob-dev-environment-05"
    await event_store.append(
        "environment_config_process_id",
        EnvironmentConfigurationProvided(
            environment_id=environment_id,
            occurred_at=time_under_control.now(),
            knowledge_base_id="test-knowledge-base-id",
            project_setup="echo 'Hello, World!'",
            user_id="test-user-id",
            process_id=environment_config_process_id,
        ),
    )
    issue_resolution_process_id = "test-process-id"
    issue_resolution_requested_event = IssueResolutionRequested(
        occurred_at=time_under_control.now(),
        knowledge_base_id="test-knowledge-base-id",
        process_id=issue_resolution_process_id,
        issue=IssueInfo(title="issue title", description="test issue"),
    )
    git_helper = Mock(spec=GitClient)
    coding_agent = AsyncMock(spec=IssueResolvingAgent)
    microvm_instance_id = "test-instance-id"
    microvm_client = Mock(spec=MorphCloudClient)
    snapshot_id = "test-snapshot-id"
    microvm_client.snapshots.list.return_value = [
        Snapshot(
            id=snapshot_id,
            object="snapshot",
            created=time_under_control.now().timestamp(),
            spec=ResourceSpec(
                vcpus=2,
                memory=4096,
                disk_size=20,
            ),
            refs=SnapshotRefs(image_id="test-image-id"),
            status=SnapshotStatus.READY,
            metadata={
                "type": "dev",
                "knowledge_base_id": "test-knowledge-base-id",
                "environment_id": environment_id,
            },
        )
    ]
    started_instance = Mock(spec=Instance)
    microvm_client.instances.start.return_value = started_instance
    started_instance.id = microvm_instance_id
    started_instance.exec.return_value = InstanceExecResponse(
        exit_code=0, stdout="success", stderr=""
    )
    os.environ.clear()
    os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-api-key"

    # When
    await process_event_message(
        issue_resolution_requested_event,
        dependencies=Dependencies(
            event_store,
            git_helper,
            coding_agent,
            time_under_control,
            microvm_client,
            is_dev_environment_service_enabled=True,
        ),
    )
    # Then
    produced_events = await event_store.get(issue_resolution_process_id)

    assert produced_events == [
        IssueResolutionEnvironmentPrepared(
            process_id=issue_resolution_process_id,
            occurred_at=time_under_control.now(),
            environment_id=environment_id,
            instance_id=microvm_instance_id,
            knowledge_base_id="test-knowledge-base-id",
        )
    ]

    microvm_client.snapshots.list.assert_called_once_with(
        metadata={
            "type": "dev",
            "knowledge_base_id": "test-knowledge-base-id",
            "environment_id": environment_id,
        }
    )
    microvm_client.instances.start.assert_called_once_with(
        snapshot_id=snapshot_id, ttl_seconds=5400
    )
    solve_settings = """
export ANTHROPIC_API_KEY=\'test-anthropic-api-key\'
export ANTHROPIC_BASE_URL=\'https://api.anthropic.com/\'
export ISSUE__DESCRIPTION=\'test issue\'
export ISSUE__TITLE=\'issue title\'
export AGENT=\'claude-code\'
export AI_MODEL=\'claude-sonnet-4\'
export AI_MODEL_VERSION=\'20250514\'
export GIT__REPOSITORY_URL=\'http://gitlab.com/test-repo.git\'
export GIT__ACCESS_TOKEN=\'s3cretAcc3ssT0k3n\'
export GIT__USER_MAIL=\'agent@umans.ai\'
export GIT__USER_NAME=\'umans-agent\'
export REPO_PATH=\'test-repo\'
export PROCESS_ID=\'test-process-id\'
"""
    started_instance.exec.assert_called_once_with(
        to_script(
            command="cudu solve",
            dotenv_settings=solve_settings,
        )
    )


@pytest.mark.asyncio
async def test_issue_resolution_should_use_vm_and_prepare_snapshot_when_env_config_script_is_provided_and_snapshot_is_missing(
    event_store, time_under_control: ControllableClock
):
    # Given
    time_under_control.set_from_iso_format("2025-01-01T00:00:00")
    repo_integration_process_id = "indexation_process_id"
    await event_store.append(
        repo_integration_process_id,
        CodeRepositoryConnected(
            url="http://gitlab.com/test-repo.git",
            access_token="s3cretAcc3ssT0k3n",
            user_id="test-user-id",
            space_id="test-space-id",
            occurred_at=time_under_control.now(),
            knowledge_base_id="test-knowledge-base-id",
            process_id=repo_integration_process_id,
        ),
    )
    environment_config_process_id = "env-config-process-id"
    environment_id = "bob-dev-environment-05"
    global_setup_script = "apt-get update && apt-get install -y python3-venv"
    await event_store.append(
        "environment_config_process_id",
        EnvironmentConfigurationProvided(
            environment_id=environment_id,
            occurred_at=time_under_control.now(),
            knowledge_base_id="test-knowledge-base-id",
            global_setup=global_setup_script,
            project_setup="echo 'Hello, World!'",
            user_id="test-user-id",
            process_id=environment_config_process_id,
        ),
    )
    issue_resolution_process_id = "test-process-id"
    issue_resolution_requested_event = IssueResolutionRequested(
        occurred_at=time_under_control.now(),
        knowledge_base_id="test-knowledge-base-id",
        process_id=issue_resolution_process_id,
        issue=IssueInfo(title="issue title", description="test issue"),
    )
    git_helper = Mock(spec=GitClient)
    coding_agent = AsyncMock(spec=IssueResolvingAgent)
    microvm_instance_id = "dev-instance-id"
    microvm_client = Mock(spec=MorphCloudClient)
    base_snapshot_id = "base-snapshot-id"
    base_snapshot = Mock(spec=Snapshot)
    microvm_client.snapshots.list.side_effect = [
        [],
        [base_snapshot],
    ]
    started_instance = Mock(spec=Instance)
    microvm_client.instances.start.return_value = started_instance
    started_instance.id = microvm_instance_id
    base_snapshot.id = base_snapshot_id
    base_snapshot.status = SnapshotStatus.READY
    dev_snapshot_id = "dev-snapshot-id"
    prepared_snapshot = Mock()
    base_snapshot.exec.return_value = prepared_snapshot
    prepared_snapshot.id = dev_snapshot_id
    started_instance.exec.return_value = InstanceExecResponse(
        exit_code=0, stdout="success", stderr=""
    )
    os.environ.clear()
    os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-api-key"

    # When
    await process_event_message(
        issue_resolution_requested_event,
        dependencies=Dependencies(
            event_store,
            git_helper,
            coding_agent,
            time_under_control,
            microvm_client,
            is_dev_environment_service_enabled=True,
        ),
    )
    # Then
    produced_events = await event_store.get(issue_resolution_process_id)

    assert produced_events == [
        IssueResolutionEnvironmentPrepared(
            process_id=issue_resolution_process_id,
            occurred_at=time_under_control.now(),
            environment_id=environment_id,
            instance_id=microvm_instance_id,
            knowledge_base_id="test-knowledge-base-id",
        )
    ]

    microvm_client.snapshots.list.assert_has_calls(
        [
            call(
                metadata={
                    "type": "dev",
                    "knowledge_base_id": "test-knowledge-base-id",
                    "environment_id": environment_id,
                }
            ),
            call(
                metadata={
                    "type": "base",
                }
            ),
        ]
    )
    prepared_snapshot.set_metadata.assert_called_once_with(
        {
            "type": "dev",
            "knowledge_base_id": "test-knowledge-base-id",
            "environment_id": environment_id,
        }
    )
    microvm_client.instances.start.assert_called_once_with(
        snapshot_id=dev_snapshot_id, ttl_seconds=5400
    )
    prepare_settings = """
export PROCESS_ID=\'test-process-id\'
export REPO_PATH=\'test-repo\'
export URL=\'http://gitlab.com/test-repo.git\'
export ACCESS_TOKEN=\'s3cretAcc3ssT0k3n\'
export ISSUE__DESCRIPTION=\'test issue\'
export ISSUE__TITLE=\'issue title\'
export INSTALL_SCRIPT=\'echo \'"\'"\'Hello, World!\'"\'"\'\'
"""
    base_snapshot.exec.assert_called_once_with(
        to_script(
            command="cudu prepare",
            dotenv_settings=prepare_settings,
            global_setup_script=global_setup_script,
        )
    )

    solve_settings = """
export ANTHROPIC_API_KEY=\'test-anthropic-api-key\'
export ANTHROPIC_BASE_URL=\'https://api.anthropic.com/\'
export ISSUE__DESCRIPTION=\'test issue\'
export ISSUE__TITLE=\'issue title\'
export AGENT=\'claude-code\'
export AI_MODEL=\'claude-sonnet-4\'
export AI_MODEL_VERSION=\'20250514\'
export GIT__REPOSITORY_URL=\'http://gitlab.com/test-repo.git\'
export GIT__ACCESS_TOKEN=\'s3cretAcc3ssT0k3n\'
export GIT__USER_MAIL=\'agent@umans.ai\'
export GIT__USER_NAME=\'umans-agent\'
export REPO_PATH=\'test-repo\'
export PROCESS_ID=\'test-process-id\'
"""
    started_instance.exec.assert_called_once_with(
        to_script(command="cudu solve", dotenv_settings=solve_settings)
    )


def to_script(
    command: str, dotenv_settings: str, global_setup_script: str | None = None
) -> str:
    return """
set -Eeuo pipefail
umask 0077
%s
trap \'rm -f "/home/umans/.cudu_env" "/home/umans/.cudu_run.sh"\' EXIT

# 1) write .env literally
cat > "/home/umans/.cudu_env" <<\'ENV\'
%s
ENV
chown umans:umans "/home/umans/.cudu_env"
chmod 600 "/home/umans/.cudu_env"

# 2) write the exec script literally (owned by umans)
cat > "/home/umans/.cudu_run.sh" <<\'SH\'
#!/bin/bash
set -Eeuo pipefail
set -a
. "/home/umans/.cudu_env"
set +a

# --- pick a safe working directory so .env is readable ---
if [ -n "${REPO_PATH:-}" ] && [ "${REPO_PATH:0:1}" = "/" ]; then
  cd "${REPO_PATH}" || cd "$HOME"
else
  cd "$HOME"
fi

# ensure PATH is sane for user invocations
export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

# quick sanity (leave for now; remove once stable)
echo "PWD=$(pwd)"; echo "PATH=$PATH"; command -v cudu >/dev/null || { echo "cudu not found" >&2; exit 127; }

exec %s | tee -a /home/umans/.cudu_run.log
SH
chown umans:umans "/home/umans/.cudu_run.sh"
chmod 700 "/home/umans/.cudu_run.sh"

# 3) run as umans without -c or -l
runuser -u umans -- /bin/bash "/home/umans/.cudu_run.sh"
""" % ((global_setup_script or "").strip(), dotenv_settings.strip(), command)
