from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from issue_solver.events.domain import CodeRepositoryConnected
from issue_solver.events.code_repo_integration import get_connected_repo_event


@pytest.mark.asyncio
async def test_get_connected_repo_event_space_only_filtering():
    """Test that get_connected_repo_event uses space-only filtering."""
    # Arrange
    mock_event_store = AsyncMock()
    space_id = "space-123"

    # Mock repository connected by a different user
    connected_event = CodeRepositoryConnected(
        url="https://github.com/example/repo",
        access_token="token-123",
        user_id="different-user-789",  # Different user connected the repo
        space_id=space_id,
        knowledge_base_id="kb-123",
        process_id="process-123",
        occurred_at=datetime(2023, 1, 1, 12, 0, 0),
    )

    mock_event_store.find.return_value = [connected_event]

    # Act
    result = await get_connected_repo_event(mock_event_store, space_id)

    # Assert
    assert result is not None
    assert result.space_id == space_id
    assert (
        result.user_id == "different-user-789"
    )  # Should find repo connected by different user

    # Verify that the query only uses space_id, not user_id
    mock_event_store.find.assert_called_once_with(
        {"space_id": space_id}, CodeRepositoryConnected
    )


@pytest.mark.asyncio
async def test_get_connected_repo_event_no_space_id():
    """Test that get_connected_repo_event returns None when space_id is missing."""
    # Arrange
    mock_event_store = AsyncMock()
    space_id = None

    # Act
    result = await get_connected_repo_event(mock_event_store, space_id)

    # Assert
    assert result is None
    mock_event_store.find.assert_not_called()


@pytest.mark.asyncio
async def test_get_connected_repo_event_no_repo_found():
    """Test that get_connected_repo_event returns None when no repository is connected to the space."""
    # Arrange
    mock_event_store = AsyncMock()
    space_id = "space-123"

    mock_event_store.find.return_value = []  # No repository connected

    # Act
    result = await get_connected_repo_event(mock_event_store, space_id)

    # Assert
    assert result is None
    mock_event_store.find.assert_called_once_with(
        {"space_id": space_id}, CodeRepositoryConnected
    )


@pytest.mark.asyncio
async def test_get_connected_repo_event_multiple_repos_returns_most_recent():
    """Test that get_connected_repo_event returns the most recent repository when multiple exist."""
    # Arrange
    mock_event_store = AsyncMock()
    space_id = "space-123"

    older_event = CodeRepositoryConnected(
        url="https://github.com/example/old-repo",
        access_token="old-token-123",
        user_id="user-789",
        space_id=space_id,
        knowledge_base_id="kb-old",
        process_id="process-old",
        occurred_at=datetime(2023, 1, 1, 12, 0, 0),
    )

    newer_event = CodeRepositoryConnected(
        url="https://github.com/example/new-repo",
        access_token="new-token-123",
        user_id="user-999",
        space_id=space_id,
        knowledge_base_id="kb-new",
        process_id="process-new",
        occurred_at=datetime(2023, 1, 2, 12, 0, 0),  # More recent
    )

    mock_event_store.find.return_value = [older_event, newer_event]

    # Act
    result = await get_connected_repo_event(mock_event_store, space_id)

    # Assert
    assert result is not None
    assert result.url == "https://github.com/example/new-repo"
    assert result.process_id == "process-new"
    mock_event_store.find.assert_called_once_with(
        {"space_id": space_id}, CodeRepositoryConnected
    )
