from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from issue_solver.events.domain import (
    CodeRepositoryConnected,
    CodeRepositoryIndexed,
    CodeRepositoryIntegrationFailed,
    RepositoryIndexationRequested,
)
from issue_solver.git_operations.git_helper import (
    GitValidationError,
)
from issue_solver.worker.indexing.delta import index_new_changes_codebase
from issue_solver.worker.indexing.full import index_codebase
from tests.fixtures import NoopGitValidationService


@pytest.mark.asyncio
async def test_index_codebase_git_validation_error():
    """Test that index_codebase handles GitValidationError correctly."""
    # Given
    process_id = "test-process-id"
    url = "https://github.com/example/repo.git"
    access_token = "test-token"
    knowledge_base_id = "test-kb-id"
    message = CodeRepositoryConnected(
        process_id=process_id,
        url=url,
        access_token=access_token,
        user_id="test-user",
        space_id="test-space",
        knowledge_base_id=knowledge_base_id,
        occurred_at="2023-01-01T00:00:00Z",
    )

    # Mock dependencies
    mock_event_store = AsyncMock()

    # Mock a GitValidationError when cloning the repository
    mock_clone = MagicMock(
        side_effect=GitValidationError(
            "Repository not found. Please check the URL.", "repository_not_found", 404
        )
    )

    # Create our AsyncMock for init_event_store that returns mock_event_store
    mock_init_event_store = AsyncMock()
    mock_init_event_store.return_value = mock_event_store

    # Patch dependencies
    with (
        patch(
            "issue_solver.worker.indexing.full.init_event_store",
            mock_init_event_store,
        ),
        patch(
            "issue_solver.worker.indexing.full.get_clock",
            return_value=MagicMock(now=lambda: "2023-01-01T01:00:00Z"),
        ),
        patch(
            "issue_solver.worker.indexing.full.get_validation_service",
            return_value=NoopGitValidationService(),
        ),
        patch(
            "issue_solver.worker.indexing.full.GitHelper.clone_repository",
            mock_clone,
        ),
    ):
        # When
        await index_codebase(message)

        # Then - Verify that CodeRepositoryConnectionFailed event was appended with correct error information
        assert mock_event_store.append.call_count == 1
        assert mock_event_store.append.call_args[0][0] == process_id
        event = mock_event_store.append.call_args[0][1]
        assert isinstance(event, CodeRepositoryIntegrationFailed)
        assert event.error_type == "repository_not_found"
        assert "Repository not found" in event.error_message
        assert event.url == url
        assert event.knowledge_base_id == knowledge_base_id
        assert event.process_id == process_id


@pytest.mark.asyncio
async def test_index_new_changes_codebase_git_validation_error():
    """Test that index_new_changes_codebase handles GitValidationError correctly."""
    # Given
    process_id = "test-process-id"
    knowledge_base_id = "test-kb-id"
    url = "https://github.com/example/repo.git"
    access_token = "test-token"
    message = RepositoryIndexationRequested(
        process_id=process_id,
        knowledge_base_id=knowledge_base_id,
        user_id="test-user",
        occurred_at="2023-01-01T00:00:00Z",
    )

    # Mock dependencies
    mock_event_store = AsyncMock()
    mock_events = [
        CodeRepositoryConnected(
            process_id=process_id,
            url=url,
            access_token=access_token,
            user_id="test-user",
            space_id="test-space",
            knowledge_base_id=knowledge_base_id,
            occurred_at="2022-12-31T00:00:00Z",
        ),
        CodeRepositoryIndexed(
            process_id=process_id,
            branch="main",
            commit_sha="abc123",
            stats={},
            knowledge_base_id=knowledge_base_id,
            occurred_at="2022-12-31T01:00:00Z",
        ),
    ]
    mock_event_store.get.return_value = mock_events

    # Mock a GitValidationError when pulling the repository
    mock_pull = MagicMock(
        side_effect=GitValidationError(
            "Permission denied. Check your access rights to this repository.",
            "permission_denied",
            403,
        )
    )

    # Patch file existence check to simulate repository already cloned
    mock_path_exists = MagicMock(return_value=True)

    # Create our AsyncMock for init_event_store that returns mock_event_store
    mock_init_event_store = AsyncMock()
    mock_init_event_store.return_value = mock_event_store

    # Patch dependencies
    with (
        patch(
            "issue_solver.worker.indexing.delta.init_event_store",
            mock_init_event_store,
        ),
        patch(
            "issue_solver.worker.indexing.delta.get_clock",
            return_value=MagicMock(now=lambda: "2023-01-01T01:00:00Z"),
        ),
        patch(
            "issue_solver.worker.indexing.delta.get_validation_service",
            return_value=NoopGitValidationService(),
        ),
        patch(
            "issue_solver.worker.indexing.delta.GitHelper.pull_repository",
            mock_pull,
        ),
        patch("pathlib.Path.exists", mock_path_exists),
    ):
        # When
        await index_new_changes_codebase(message)

        # Then - Verify that CodeRepositoryConnectionFailed event was appended with correct error information
        assert mock_event_store.append.call_count == 1
        event = mock_event_store.append.call_args[0][1]
        assert isinstance(event, CodeRepositoryIntegrationFailed)
        assert event.error_type == "permission_denied"
        assert "Permission denied" in event.error_message
        assert event.url == url
        assert event.knowledge_base_id == knowledge_base_id
        assert event.process_id == process_id


@pytest.mark.asyncio
async def test_index_new_changes_codebase_clone_git_validation_error():
    """Test that index_new_changes_codebase handles GitValidationError during cloning."""
    # Given
    process_id = "test-process-id"
    knowledge_base_id = "test-kb-id"
    url = "https://github.com/example/repo.git"
    access_token = "test-token"
    message = RepositoryIndexationRequested(
        process_id=process_id,
        knowledge_base_id=knowledge_base_id,
        user_id="test-user",
        occurred_at="2023-01-01T00:00:00Z",
    )

    # Mock dependencies
    mock_event_store = AsyncMock()
    mock_events = [
        CodeRepositoryConnected(
            process_id=process_id,
            url=url,
            access_token=access_token,
            user_id="test-user",
            space_id="test-space",
            knowledge_base_id=knowledge_base_id,
            occurred_at="2022-12-31T00:00:00Z",
        ),
        CodeRepositoryIndexed(
            process_id=process_id,
            branch="main",
            commit_sha="abc123",
            stats={},
            knowledge_base_id=knowledge_base_id,
            occurred_at="2022-12-31T01:00:00Z",
        ),
    ]
    mock_event_store.get.return_value = mock_events

    # Mock a GitValidationError when cloning the repository
    mock_clone = MagicMock(
        side_effect=GitValidationError(
            "Unable to access repository. Check the URL and your internet connection.",
            "repository_unavailable",
            502,
        )
    )

    # Patch file existence check to simulate repository not yet cloned
    mock_path_exists = MagicMock(return_value=False)

    # Create our AsyncMock for init_event_store that returns mock_event_store
    mock_init_event_store = AsyncMock()
    mock_init_event_store.return_value = mock_event_store

    # Patch dependencies
    with (
        patch(
            "issue_solver.worker.indexing.delta.init_event_store",
            mock_init_event_store,
        ),
        patch(
            "issue_solver.worker.indexing.delta.get_clock",
            return_value=MagicMock(now=lambda: "2023-01-01T01:00:00Z"),
        ),
        patch(
            "issue_solver.worker.indexing.delta.get_validation_service",
            return_value=NoopGitValidationService(),
        ),
        patch(
            "issue_solver.worker.indexing.delta.GitHelper.clone_repository",
            mock_clone,
        ),
        patch("pathlib.Path.exists", mock_path_exists),
    ):
        # When
        await index_new_changes_codebase(message)

        # Then - Verify that CodeRepositoryConnectionFailed event was appended with correct error information
        assert mock_event_store.append.call_count == 1
        event = mock_event_store.append.call_args[0][1]
        assert isinstance(event, CodeRepositoryIntegrationFailed)
        assert event.error_type == "repository_unavailable"
        assert "Unable to access repository" in event.error_message
        assert event.url == url
        assert event.knowledge_base_id == knowledge_base_id
        assert event.process_id == process_id
