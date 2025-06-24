from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from issue_solver.events.domain import CodeRepositoryConnected
from issue_solver.git_operations.git_helper import GitValidationError
from issue_solver.webapi.payloads import ConnectRepositoryRequest, RotateTokenRequest
from issue_solver.webapi.routers.repository import connect_repository, rotate_token


@pytest.fixture
def mock_validation_service():
    """Create a mock validation service for testing."""
    return Mock()


@pytest.fixture
def connect_repository_request():
    """Create a sample repository connection request."""
    return ConnectRepositoryRequest(
        url="https://github.com/example/repo.git",
        access_token="test-token",
        space_id="test-space",
    )


@pytest.fixture
def event_store():
    """Create a mock event store for testing."""
    store = AsyncMock()
    store.append = AsyncMock()
    return store


@pytest.mark.asyncio
async def test_connect_repository_authentication_error(
    mock_validation_service,
    connect_repository_request,
    event_store,
):
    """Test that authentication errors are handled correctly."""
    # Given
    mock_validation_service.validate_repository_access.side_effect = GitValidationError(
        "Authentication failed. Please check your access token.",
        "authentication_failed",
        401,
    )

    mock_clock = Mock(now=lambda: "2023-01-01T00:00:00Z")
    mock_logger = Mock()

    # When/Then - expect HTTPException with status_code 401
    with pytest.raises(HTTPException) as exc_info:
        await connect_repository(
            connect_repository_request=connect_repository_request,
            user_id="test-user",
            event_store=event_store,
            logger=mock_logger,
            clock=mock_clock,
            validation_service=mock_validation_service,
        )

    # Verify exception details
    assert exc_info.value.status_code == 401
    assert "Authentication failed" in exc_info.value.detail

    # Verify validation service was called with correct parameters
    mock_validation_service.validate_repository_access.assert_called_once_with(
        connect_repository_request.url, connect_repository_request.access_token
    )

    # Verify no events were appended (error happened before that)
    event_store.append.assert_not_called()


@pytest.mark.asyncio
async def test_connect_repository_not_found_error(
    mock_validation_service,
    connect_repository_request,
    event_store,
):
    """Test that repository not found errors are handled correctly."""
    # Given
    mock_validation_service.validate_repository_access.side_effect = GitValidationError(
        "Repository not found. Please check the URL.",
        "repository_not_found",
        404,
    )

    mock_clock = Mock(now=lambda: "2023-01-01T00:00:00Z")
    mock_logger = Mock()

    # When/Then - expect HTTPException with status_code 404
    with pytest.raises(HTTPException) as exc_info:
        await connect_repository(
            connect_repository_request=connect_repository_request,
            user_id="test-user",
            event_store=event_store,
            logger=mock_logger,
            clock=mock_clock,
            validation_service=mock_validation_service,
        )

    # Verify exception details
    assert exc_info.value.status_code == 404
    assert "Repository not found" in exc_info.value.detail


@pytest.fixture
def rotate_token_request():
    """Create a sample token rotation request."""
    return RotateTokenRequest(access_token="new-test-token")


@pytest.fixture
def existing_repository_connection():
    """Create a sample existing repository connection."""
    return CodeRepositoryConnected(
        url="https://github.com/example/repo.git",
        access_token="old-test-token",
        user_id="test-user",
        space_id="test-space",
        knowledge_base_id="kb-123",
        process_id="proc-123",
        occurred_at=datetime.fromisoformat("2023-01-01T00:00:00Z"),
    )


@pytest.mark.asyncio
async def test_rotate_token_success(
    rotate_token_request,
    existing_repository_connection,
):
    """Test successful token rotation."""
    # Given
    mock_event_store = AsyncMock()
    mock_event_store.find.return_value = [existing_repository_connection]
    mock_event_store.append = AsyncMock()

    mock_validation_service = Mock()
    mock_validation_service.validate_repository_access.return_value = None

    mock_clock = Mock(now=lambda: "2023-01-02T00:00:00Z")
    mock_logger = Mock()

    # When
    result = await rotate_token(
        knowledge_base_id="kb-123",
        rotate_token_request=rotate_token_request,
        user_id="test-user",
        event_store=mock_event_store,
        logger=mock_logger,
        clock=mock_clock,
        validation_service=mock_validation_service,
    )

    # Then
    assert result["message"] == "Token rotated successfully"
    assert "token_permissions" in result

    # Verify event store interactions
    mock_event_store.find.assert_called_once_with(
        {"knowledge_base_id": "kb-123"}, CodeRepositoryConnected
    )
    mock_event_store.append.assert_called_once()

    # Verify validation was called with new token
    mock_validation_service.validate_repository_access.assert_called_once_with(
        existing_repository_connection.url, rotate_token_request.access_token
    )


@pytest.mark.asyncio
async def test_rotate_token_repository_not_found(
    rotate_token_request,
):
    """Test token rotation when repository is not found."""
    # Given
    mock_event_store = AsyncMock()
    mock_event_store.find.return_value = []

    mock_validation_service = Mock()
    mock_clock = Mock()
    mock_logger = Mock()

    # When/Then
    with pytest.raises(HTTPException) as exc_info:
        await rotate_token(
            knowledge_base_id="nonexistent-kb",
            rotate_token_request=rotate_token_request,
            user_id="test-user",
            event_store=mock_event_store,
            logger=mock_logger,
            clock=mock_clock,
            validation_service=mock_validation_service,
        )

    assert exc_info.value.status_code == 404
    assert "No repository found" in exc_info.value.detail

    # Verify no validation was attempted
    mock_validation_service.validate_repository_access.assert_not_called()


@pytest.mark.asyncio
async def test_rotate_token_validation_failure(
    rotate_token_request,
    existing_repository_connection,
):
    """Test token rotation when new token validation fails."""
    # Given
    mock_event_store = AsyncMock()
    mock_event_store.find.return_value = [existing_repository_connection]

    mock_validation_service = Mock()
    mock_validation_service.validate_repository_access.side_effect = GitValidationError(
        "New token is invalid",
        "authentication_failed",
        401,
    )

    mock_clock = Mock()
    mock_logger = Mock()

    # When/Then
    with pytest.raises(HTTPException) as exc_info:
        await rotate_token(
            knowledge_base_id="kb-123",
            rotate_token_request=rotate_token_request,
            user_id="test-user",
            event_store=mock_event_store,
            logger=mock_logger,
            clock=mock_clock,
            validation_service=mock_validation_service,
        )

    assert exc_info.value.status_code == 401
    assert "New token is invalid" in exc_info.value.detail

    # Verify no event was appended (validation failed)
    mock_event_store.append.assert_not_called()
