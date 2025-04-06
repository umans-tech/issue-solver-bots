import pytest
from unittest.mock import patch, Mock, AsyncMock

from fastapi import HTTPException
from fastapi.testclient import TestClient

from issue_solver.git_operations.git_helper import GitValidationError
from issue_solver.webapi.routers.repository import connect_repository
from issue_solver.webapi.payloads import ConnectRepositoryRequest


class TestRepositoryRouterErrorHandling:
    """Tests for error handling in the repository router."""

    @pytest.fixture
    def mock_validation_service(self):
        """Create a mock validation service for testing."""
        return Mock()

    @pytest.fixture
    def connect_repository_request(self):
        """Create a sample repository connection request."""
        return ConnectRepositoryRequest(
            url="https://github.com/example/repo.git",
            access_token="test-token",
            user_id="test-user",
            space_id="test-space",
        )

    @pytest.fixture
    def event_store(self):
        """Create a mock event store for testing."""
        store = AsyncMock()
        store.append = AsyncMock()
        return store

    @pytest.fixture
    def openai_client_mock(self):
        """Create a mock OpenAI client for testing."""
        client = Mock()
        client.vector_stores.create.return_value = Mock(id="test-vector-store-id")
        return client

    @pytest.mark.asyncio
    @patch("issue_solver.webapi.routers.repository.OpenAI")
    async def test_connect_repository_authentication_error(
        self,
        mock_openai,
        mock_validation_service,
        connect_repository_request,
        event_store,
    ):
        """Test that authentication errors are handled correctly."""
        # Given
        mock_validation_service.validate_repository_access.side_effect = (
            GitValidationError(
                "Authentication failed. Please check your access token.",
                "authentication_failed",
                401,
            )
        )

        mock_openai.return_value = Mock()
        mock_clock = Mock(now=lambda: "2023-01-01T00:00:00Z")
        mock_logger = Mock()

        # When/Then - expect HTTPException with status_code 401
        with pytest.raises(HTTPException) as exc_info:
            await connect_repository(
                connect_repository_request=connect_repository_request,
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
            connect_repository_request.url,
            connect_repository_request.access_token,
            mock_logger,
        )

        # Verify no events were appended (error happened before that)
        event_store.append.assert_not_called()
        # Verify OpenAI client was not created (error happened before that)
        mock_openai.assert_not_called()

    @pytest.mark.asyncio
    @patch("issue_solver.webapi.routers.repository.OpenAI")
    async def test_connect_repository_not_found_error(
        self,
        mock_openai,
        mock_validation_service,
        connect_repository_request,
        event_store,
    ):
        """Test that repository not found errors are handled correctly."""
        # Given
        mock_validation_service.validate_repository_access.side_effect = (
            GitValidationError(
                "Repository not found. Please check the URL.",
                "repository_not_found",
                404,
            )
        )

        mock_openai.return_value = Mock()
        mock_clock = Mock(now=lambda: "2023-01-01T00:00:00Z")
        mock_logger = Mock()

        # When/Then - expect HTTPException with status_code 404
        with pytest.raises(HTTPException) as exc_info:
            await connect_repository(
                connect_repository_request=connect_repository_request,
                event_store=event_store,
                logger=mock_logger,
                clock=mock_clock,
                validation_service=mock_validation_service,
            )

        # Verify exception details
        assert exc_info.value.status_code == 404
        assert "Repository not found" in exc_info.value.detail

    # Integration test with the FastAPI app
    @patch("issue_solver.webapi.dependencies.get_validation_service")
    @patch("issue_solver.webapi.routers.repository.OpenAI")
    def test_connect_repository_endpoint_validation_error(
        self, mock_openai, mock_get_validation_service, connect_repository_request
    ):
        """Integration test for the repository connection endpoint with validation error."""
        # Given
        mock_validation_service = Mock()
        mock_validation_service.validate_repository_access.side_effect = (
            GitValidationError(
                "Authentication failed. Please check your access token.",
                "authentication_failed",
                401,
            )
        )
        mock_get_validation_service.return_value = mock_validation_service

        # Create a test app with manually initialized event_store
        from fastapi import FastAPI

        test_app = FastAPI()
        test_app.state.event_store = AsyncMock()

        # Override the router dependency to use our mocked event_store
        from issue_solver.webapi.routers import repository as repo_module

        with patch.object(
            repo_module, "get_event_store", return_value=test_app.state.event_store
        ):
            # Include our router
            test_app.include_router(repo_module.router)

            # Create a test client with our custom app
            client = TestClient(test_app)

            # When
            response = client.post(
                "/repositories/",
                json={
                    "url": connect_repository_request.url,
                    "access_token": connect_repository_request.access_token,
                    "user_id": connect_repository_request.user_id,
                    "space_id": connect_repository_request.space_id,
                },
            )

            # Then
            assert response.status_code == 401
            response_data = response.json()
            assert "Authentication failed" in response_data["detail"]
