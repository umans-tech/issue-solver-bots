from datetime import datetime
from unittest.mock import Mock, AsyncMock

import pytest

from tests.controllable_clock import ControllableClock

from issue_solver.agents.issue_resolving_agent import IssueResolvingAgent
from issue_solver.events.domain import (
    IssueResolutionStarted,
    IssueResolutionRequested,
    IssueResolutionCompleted,
    IssueResolutionFailed,
    CodeRepositoryConnected,
)
from issue_solver.git_operations.git_helper import GitClient, PullRequestReference
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
