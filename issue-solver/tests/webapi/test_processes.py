from datetime import datetime

from issue_solver.events.domain import (
    CodeRepositoryConnected,
    CodeRepositoryIndexed,
    RepositoryIndexationRequested,
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
