from datetime import datetime

from issue_solver.events.domain import (
    CodeRepositoryConnected,
    CodeRepositoryTokenRotated,
    CodeRepositoryIndexed,
    RepositoryIndexationRequested,
    IssueResolutionRequested,
    IssueResolutionStarted,
    IssueResolutionCompleted,
    IssueResolutionFailed,
)
from issue_solver.webapi.routers.processes import ProcessTimelineView


def test_status_should_be_connected_latest_event_is_connected():
    # Given
    history = [
        CodeRepositoryConnected(
            url="https://api.github.com",
            access_token="test-access-token",
            user_id="test-user-id",
            space_id="test-space-id",
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
        )
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.status == "connected"


def test_status_should_be_indexed_if_latest_event_is_indexed():
    # Given
    history = [
        CodeRepositoryConnected(
            url="https://api.github.com",
            access_token="test-access-token",
            user_id="test-user-id",
            space_id="test-space-id",
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T00:00:00"),
        ),
        CodeRepositoryIndexed(
            branch="main",
            commit_sha="test-commit-sha",
            stats={"test": "stats"},
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T01:00:00"),
        ),
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.status == "indexed"


def test_status_should_be_indexing_if_the_latest_event_is_indexation_requested():
    # Given
    history = [
        CodeRepositoryConnected(
            url="https://api.github.com",
            access_token="test-access-token",
            user_id="test-user-id",
            space_id="test-space-id",
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T00:00:00"),
        ),
        CodeRepositoryIndexed(
            branch="main",
            commit_sha="test-commit-sha",
            stats={"test": "stats"},
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T01:00:00"),
        ),
        RepositoryIndexationRequested(
            occurred_at=datetime.fromisoformat("2025-01-01T02:00:00"),
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            user_id="test-user-id",
        ),
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.status == "indexing"


def test_status_should_be_indexed_if_the_latest_event_is_indexed_after_indexation_requested():
    # Given
    history = [
        CodeRepositoryConnected(
            url="https://api.github.com",
            access_token="test-access-token",
            user_id="test-user-id",
            space_id="test-space-id",
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T00:00:00"),
        ),
        CodeRepositoryIndexed(
            branch="main",
            commit_sha="test-commit-sha",
            stats={"test": "stats"},
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T01:00:00"),
        ),
        RepositoryIndexationRequested(
            occurred_at=datetime.fromisoformat("2025-01-01T02:00:00"),
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            user_id="test-user-id",
        ),
        CodeRepositoryIndexed(
            branch="main",
            commit_sha="test-commit-sha",
            stats={"test": "stats"},
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T03:00:00"),
        ),
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.status == "indexed"


def test_status_should_be_started_when_the_latest_event_is_issue_resolution_in_progress():
    # Given
    history = [
        IssueResolutionRequested(
            knowledge_base_id="knowledge-base-id",
            issue={
                "description": "test-issue-description",
                "title": "test-issue-title",
            },
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T00:00:00"),
        ),
        IssueResolutionStarted(
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T01:00:00"),
        ),
    ]
    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.type == "issue_resolution"
    assert process_timeline_view.status == "in_progress"


def test_status_should_be_completed_when_the_latest_event_is_issue_resolution_completed():
    # Given
    history = [
        IssueResolutionRequested(
            knowledge_base_id="knowledge-base-id",
            issue={
                "description": "test-issue-description",
                "title": "test-issue-title",
            },
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T00:00:00"),
        ),
        IssueResolutionStarted(
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T01:00:00"),
        ),
        IssueResolutionCompleted(
            pr_url="test-pr-url",
            pr_number=123,
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T02:00:00"),
        ),
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.type == "issue_resolution"
    assert process_timeline_view.status == "completed"


def test_status_should_be_failed_when_the_latest_event_is_issue_resolution_failed():
    # Given
    history = [
        IssueResolutionRequested(
            knowledge_base_id="knowledge-base-id",
            issue={
                "description": "test-issue-description",
                "title": "test-issue-title",
            },
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T00:00:00"),
        ),
        IssueResolutionStarted(
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T01:00:00"),
        ),
        IssueResolutionFailed(
            reason="test-reason",
            error_message="test-error-message",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2025-01-01T02:00:00"),
        ),
    ]
    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.type == "issue_resolution"
    assert process_timeline_view.status == "failed"


def test_status_should_remain_connected_after_token_rotation():
    # Given
    history = [
        CodeRepositoryConnected(
            url="https://api.github.com",
            access_token="test-access-token",
            user_id="test-user-id",
            space_id="test-space-id",
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
        ),
        CodeRepositoryTokenRotated(
            knowledge_base_id="knowledge-base-id",
            new_access_token="new-test-token",
            user_id="test-user-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2021-01-01T01:00:00"),
        ),
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.status == "connected"


def test_status_should_remain_indexed_after_token_rotation():
    # Given
    history = [
        CodeRepositoryConnected(
            url="https://api.github.com",
            access_token="test-access-token",
            user_id="test-user-id",
            space_id="test-space-id",
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
        ),
        CodeRepositoryIndexed(
            branch="main",
            commit_sha="test-commit-sha",
            stats={"test": "stats"},
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2021-01-01T01:00:00"),
        ),
        CodeRepositoryTokenRotated(
            knowledge_base_id="knowledge-base-id",
            new_access_token="new-test-token",
            user_id="test-user-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2021-01-01T02:00:00"),
        ),
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.status == "indexed"


def test_status_should_remain_indexing_after_token_rotation():
    # Given
    history = [
        CodeRepositoryConnected(
            url="https://api.github.com",
            access_token="test-access-token",
            user_id="test-user-id",
            space_id="test-space-id",
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
        ),
        CodeRepositoryIndexed(
            branch="main",
            commit_sha="test-commit-sha",
            stats={"test": "stats"},
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2021-01-01T01:00:00"),
        ),
        RepositoryIndexationRequested(
            occurred_at=datetime.fromisoformat("2021-01-01T02:00:00"),
            knowledge_base_id="knowledge-base-id",
            process_id="test-process-id",
            user_id="test-user-id",
        ),
        CodeRepositoryTokenRotated(
            knowledge_base_id="knowledge-base-id",
            new_access_token="new-test-token",
            user_id="test-user-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2021-01-01T03:00:00"),
        ),
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.status == "indexing"


def test_status_should_be_unknown_when_only_token_rotation_events():
    # Given - Only token rotation events (edge case)
    history = [
        CodeRepositoryTokenRotated(
            knowledge_base_id="knowledge-base-id",
            new_access_token="new-test-token",
            user_id="test-user-id",
            process_id="test-process-id",
            occurred_at=datetime.fromisoformat("2021-01-01T00:00:00"),
        ),
    ]

    # When
    process_timeline_view = ProcessTimelineView.create_from(
        process_id="test-process-id", events=history
    )

    # Then
    assert process_timeline_view.status == "unknown"
