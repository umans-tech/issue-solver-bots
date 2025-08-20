"""Test that the most recent access token is used for git operations."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from issue_solver.events.domain import (
    CodeRepositoryConnected,
    CodeRepositoryTokenRotated,
    IssueResolutionRequested,
)
from issue_solver.events.code_repo_integration import get_most_recent_access_token
from issue_solver.git_operations.git_helper import GitClient
from issue_solver.issues.issue import IssueInfo
from issue_solver.worker.solving.process_issue_resolution_request import (
    Dependencies,
    resolve_issue,
)
from tests.controllable_clock import ControllableClock


def test_get_most_recent_access_token_with_only_connected_event():
    """Test getting token from CodeRepositoryConnected event only."""
    events = [
        CodeRepositoryConnected(
            occurred_at=datetime(2023, 1, 1, 10, 0, 0),
            url="https://github.com/test/repo",
            access_token="original_token",
            user_id="test-user",
            space_id="test-space",
            knowledge_base_id="kb-123",
            process_id="proc-123",
        )
    ]

    token = get_most_recent_access_token(events)
    assert token == "original_token"


def test_get_most_recent_access_token_with_token_rotation():
    """Test getting token from most recent event when token was rotated."""
    events = [
        CodeRepositoryConnected(
            occurred_at=datetime(2023, 1, 1, 10, 0, 0),
            url="https://github.com/test/repo",
            access_token="original_token",
            user_id="test-user",
            space_id="test-space",
            knowledge_base_id="kb-123",
            process_id="proc-123",
        ),
        CodeRepositoryTokenRotated(
            occurred_at=datetime(2023, 1, 1, 11, 0, 0),
            knowledge_base_id="kb-123",
            new_access_token="rotated_token",
            user_id="test-user",
            process_id="proc-123",
        ),
    ]

    token = get_most_recent_access_token(events)
    assert token == "rotated_token"


def test_get_most_recent_access_token_with_multiple_rotations():
    """Test getting token from most recent rotation when multiple rotations occurred."""
    events = [
        CodeRepositoryConnected(
            occurred_at=datetime(2023, 1, 1, 10, 0, 0),
            url="https://github.com/test/repo",
            access_token="original_token",
            user_id="test-user",
            space_id="test-space",
            knowledge_base_id="kb-123",
            process_id="proc-123",
        ),
        CodeRepositoryTokenRotated(
            occurred_at=datetime(2023, 1, 1, 11, 0, 0),
            knowledge_base_id="kb-123",
            new_access_token="first_rotation",
            user_id="test-user",
            process_id="proc-123",
        ),
        CodeRepositoryTokenRotated(
            occurred_at=datetime(2023, 1, 1, 12, 0, 0),
            knowledge_base_id="kb-123",
            new_access_token="second_rotation",
            user_id="test-user",
            process_id="proc-123",
        ),
    ]

    token = get_most_recent_access_token(events)
    assert token == "second_rotation"


def test_get_most_recent_access_token_empty_events():
    """Test getting token when no events are provided."""
    events = []
    token = get_most_recent_access_token(events)
    assert token is None


@pytest.mark.asyncio
async def test_resolve_issue_uses_most_recent_token(
    event_store, time_under_control: ControllableClock
):
    """Test that resolve_issue uses the most recent token from token rotation."""
    time_under_control.set_from_iso_format("2025-05-13T10:38:49")

    # Setup: Create repository connection and token rotation events
    indexation_process_id = "indexation_process_id"
    await event_store.append(
        indexation_process_id,
        CodeRepositoryConnected(
            url="test-url",
            access_token="original_token",
            user_id="test-user-id",
            space_id="test-space-id",
            occurred_at=datetime.fromisoformat("2025-05-13T10:35:00"),
            knowledge_base_id="test-knowledge-base-id",
            process_id=indexation_process_id,
        ),
    )

    # Add token rotation event with new token
    await event_store.append(
        indexation_process_id,
        CodeRepositoryTokenRotated(
            occurred_at=datetime.fromisoformat("2025-05-13T10:36:00"),
            knowledge_base_id="test-knowledge-base-id",
            new_access_token="rotated_token",
            user_id="test-user-id",
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

    # Mock git client to capture the token used
    git_client = Mock(spec=GitClient)
    captured_token = None

    def capture_clone_token(process_id, repo_path, url, access_token, issue):
        nonlocal captured_token
        captured_token = access_token

    git_client.clone_repo_and_branch.side_effect = capture_clone_token

    coding_agent = AsyncMock()

    # When
    await resolve_issue(
        issue_resolution_requested_event,
        dependencies=Dependencies(
            event_store, git_client, coding_agent, time_under_control
        ),
    )

    # Then - verify the rotated token was used, not the original
    assert captured_token == "rotated_token"
    git_client.clone_repo_and_branch.assert_called_once()
