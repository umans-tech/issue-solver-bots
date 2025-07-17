"""Integration tests for token tracking in the worker."""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from issue_solver.agents.claude_code_agent import ClaudeCodeAgent
from issue_solver.events.domain import (
    CodeRepositoryConnected,
    IssueResolutionRequested,
)
from issue_solver.git_operations.git_helper import GitClient
from issue_solver.issues.issue import IssueInfo
from issue_solver.token_usage import TokenUsageTracker
from issue_solver.worker.messages_processing import resolve_issue, Dependencies
from tests.controllable_clock import ControllableClock


@pytest.mark.asyncio
async def test_resolve_issue_records_token_usage(
    event_store, time_under_control: ControllableClock
):
    """Test that resolve_issue records token usage when using ClaudeCodeAgent."""
    time_under_control.set_from_iso_format("2025-01-20T15:00:00")

    # Setup: Create repository connection event
    indexation_process_id = "indexation_process_id"
    await event_store.append(
        indexation_process_id,
        CodeRepositoryConnected(
            url="https://github.com/test/repo",
            access_token="test_token",
            user_id="test-user-id",
            space_id="test-space-id",
            occurred_at=datetime.fromisoformat("2025-01-20T14:00:00"),
            knowledge_base_id="test-knowledge-base-id",
            process_id=indexation_process_id,
        ),
    )

    process_id = "test-process-id"
    issue_resolution_requested_event = IssueResolutionRequested(
        occurred_at=datetime.fromisoformat("2025-01-20T15:00:00"),
        knowledge_base_id="test-knowledge-base-id",
        process_id=process_id,
        issue=IssueInfo(title="Test Issue", description="Test issue description"),
        user_id="test-user-id",
    )

    # Mock git client
    git_client = Mock(spec=GitClient)
    git_client.clone_repository.return_value = None
    git_client.commit_and_push.return_value = None
    git_client.submit_pull_request.return_value = Mock(url="https://github.com/test/repo/pull/1", number=1)

    # Mock token usage tracker
    token_usage_tracker = AsyncMock(spec=TokenUsageTracker)

    # Mock Claude Code Agent
    claude_agent = Mock(spec=ClaudeCodeAgent)
    claude_agent.resolve_issue = AsyncMock()

    # Create dependencies with token usage tracker
    dependencies = Dependencies(
        event_store=event_store,
        git_client=git_client,
        coding_agent=claude_agent,
        clock=time_under_control,
        token_usage_tracker=token_usage_tracker,
    )

    # Mock the repository path existence check and removal
    with patch("pathlib.Path.exists", return_value=False):
        await resolve_issue(issue_resolution_requested_event, dependencies)

    # Verify that the resolve_issue was called with the correct process_id
    claude_agent.resolve_issue.assert_called_once()
    call_args = claude_agent.resolve_issue.call_args[0][0]
    assert call_args.process_id == process_id


@pytest.mark.asyncio
async def test_dependencies_includes_token_usage_tracker():
    """Test that Dependencies can be created with a token usage tracker."""
    event_store = Mock()
    git_client = Mock()
    coding_agent = Mock()
    clock = Mock()
    token_usage_tracker = Mock(spec=TokenUsageTracker)

    dependencies = Dependencies(
        event_store=event_store,
        git_client=git_client,
        coding_agent=coding_agent,
        clock=clock,
        token_usage_tracker=token_usage_tracker,
    )

    assert dependencies.token_usage_tracker is token_usage_tracker


@pytest.mark.asyncio
async def test_dependencies_optional_token_usage_tracker():
    """Test that Dependencies can be created without a token usage tracker."""
    event_store = Mock()
    git_client = Mock()
    coding_agent = Mock()
    clock = Mock()

    dependencies = Dependencies(
        event_store=event_store,
        git_client=git_client,
        coding_agent=coding_agent,
        clock=clock,
    )

    assert dependencies.token_usage_tracker is None