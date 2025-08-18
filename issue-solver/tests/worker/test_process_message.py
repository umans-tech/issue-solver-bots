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
)

from tests.controllable_clock import ControllableClock

from issue_solver.agents.issue_resolving_agent import IssueResolvingAgent
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
from issue_solver.worker.messages_processing import process_event_message, Dependencies


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
            script="echo 'Hello, World!'",
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
    os.environ.clear()
    os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-api-key"

    # When
    await process_event_message(
        issue_resolution_requested_event,
        dependencies=Dependencies(
            event_store, git_helper, coding_agent, time_under_control, microvm_client
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
    microvm_client.instances.start.assert_called_once_with(snapshot_id=snapshot_id)
    solve_command = (
        "runuser -l umans -c '"
        'export ANTHROPIC_API_KEY="test-anthropic-api-key" && export ANTHROPIC_BASE_URL="https://api.anthropic.com/v1" && '
        "export ISSUE=\"{'description': 'test issue', 'title': 'issue title'}\" && "
        'export AGENT="claude-code" && '
        'export AI_MODEL="claude-sonnet-4" && export AI_MODEL_VERSION="20250514" && '
        "export GIT=\"{'repository_url': 'http://gitlab.com/test-repo.git', 'access_token': 's3cretAcc3ssT0k3n', 'user_mail': 'agent@umans.ai', 'user_name': 'umans-agent'}\" && "
        'export REPO_PATH="test-repo" && '
        'export PROCESS_ID="test-process-id" && '
        "cudu solve'"
    )
    started_instance.exec.assert_called_once_with(solve_command)


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
    await event_store.append(
        "environment_config_process_id",
        EnvironmentConfigurationProvided(
            environment_id=environment_id,
            occurred_at=time_under_control.now(),
            knowledge_base_id="test-knowledge-base-id",
            script="echo 'Hello, World!'",
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
    base_snapshot.setup.return_value = Snapshot(
        id=dev_snapshot_id,
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
    os.environ.clear()
    os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-api-key"

    # When
    await process_event_message(
        issue_resolution_requested_event,
        dependencies=Dependencies(
            event_store, git_helper, coding_agent, time_under_control, microvm_client
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
    microvm_client.instances.start.assert_called_once_with(snapshot_id=dev_snapshot_id)
    prepare_command = "runuser -l umans -c 'export PROCESS_ID=\"test-process-id\" && export REPO_PATH=\"test-repo\" && export URL=\"http://gitlab.com/test-repo.git\" && export ACCESS_TOKEN=\"s3cretAcc3ssT0k3n\" && export ISSUE=\"{'description': 'test issue', 'title': 'issue title'}\" && export INSTALL_SCRIPT=\"echo 'Hello, World!'\"  && cudu prepare'"
    base_snapshot.setup.assert_called_once_with(prepare_command)

    solve_command = (
        "runuser -l umans -c '"
        'export ANTHROPIC_API_KEY="test-anthropic-api-key" && export ANTHROPIC_BASE_URL="https://api.anthropic.com/v1" && '
        "export ISSUE=\"{'description': 'test issue', 'title': 'issue title'}\" && "
        'export AGENT="claude-code" && '
        'export AI_MODEL="claude-sonnet-4" && export AI_MODEL_VERSION="20250514" && '
        "export GIT=\"{'repository_url': 'http://gitlab.com/test-repo.git', 'access_token': 's3cretAcc3ssT0k3n', 'user_mail': 'agent@umans.ai', 'user_name': 'umans-agent'}\" && "
        'export REPO_PATH="test-repo" && '
        'export PROCESS_ID="test-process-id" && '
        "cudu solve'"
    )
    started_instance.exec.assert_called_once_with(solve_command)
