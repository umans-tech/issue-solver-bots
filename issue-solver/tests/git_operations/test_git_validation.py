from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import git
import pytest
from issue_solver.git_operations.git_helper import (
    CodeVersion,
    DefaultGitValidationService,
    GitHelper,
    GitSettings,
    GitValidationError,
)
from tests.fixtures import NoopGitValidationService


@pytest.fixture
def git_settings():
    """Create GitSettings for testing."""
    return GitSettings(
        repository_url="https://github.com/example/repo.git",
        access_token="test_token",
        user_mail="test@example.com",
        user_name="Test User",
    )


class TestGitValidationService:
    @patch("issue_solver.git_operations.git_helper.cmd.Git")
    def test_default_validation_service_success(self, mock_git_cmd, git_settings):
        # Given
        service = DefaultGitValidationService()
        mock_git = MagicMock()
        mock_git.execute.return_value = ""
        mock_git_cmd.return_value = mock_git

        # When
        service.validate_repository_access(
            git_settings.repository_url, git_settings.access_token
        )

        # Then
        mock_git.execute.assert_called_once()

    @patch("issue_solver.git_operations.git_helper.cmd.Git")
    def test_default_validation_service_authentication_failed(
        self, mock_git_cmd, git_settings
    ):
        # Given
        service = DefaultGitValidationService()
        mock_git = MagicMock()
        mock_git.execute.side_effect = git.exc.GitCommandError(
            "git ls-remote",
            128,
            "stderr: Authentication failed for 'https://github.com/example/repo.git'",
        )
        mock_git_cmd.return_value = mock_git

        # When/Then
        with pytest.raises(GitValidationError) as exc_info:
            service.validate_repository_access(
                git_settings.repository_url, git_settings.access_token
            )

        # Verify error details
        error = exc_info.value
        assert error.error_type == "authentication_failed"
        assert "Authentication failed" in error.message
        assert error.status_code == 401

    @patch("issue_solver.git_operations.git_helper.cmd.Git")
    def test_default_validation_service_repo_not_found(
        self, mock_git_cmd, git_settings
    ):
        # Given
        service = DefaultGitValidationService()
        mock_git = MagicMock()
        mock_git.execute.side_effect = git.exc.GitCommandError(
            "git ls-remote",
            128,
            "stderr: Repository not found: 'https://github.com/example/repo.git'",
        )
        mock_git_cmd.return_value = mock_git

        # When/Then
        with pytest.raises(GitValidationError) as exc_info:
            service.validate_repository_access(
                git_settings.repository_url, git_settings.access_token
            )

        # Verify error details
        error = exc_info.value
        assert error.error_type == "repository_not_found"
        assert "Repository not found" in error.message
        assert error.status_code == 404

    @patch("issue_solver.git_operations.git_helper.cmd.Git")
    def test_default_validation_service_repo_unavailable(
        self, mock_git_cmd, git_settings
    ):
        """Test that DefaultGitValidationService handles repository unavailable errors correctly."""
        # Given
        service = DefaultGitValidationService()
        mock_git = MagicMock()
        mock_git.execute.side_effect = git.exc.GitCommandError(
            "git ls-remote",
            128,
            "stderr: unable to access 'https://github.com/example/repo.git'",
        )
        mock_git_cmd.return_value = mock_git

        # When/Then
        with pytest.raises(GitValidationError) as exc_info:
            service.validate_repository_access(
                git_settings.repository_url, git_settings.access_token
            )

        # Verify error details
        error = exc_info.value
        assert error.error_type == "repository_unavailable"
        assert "Could not access" in error.message
        assert error.status_code == 502

    @patch("issue_solver.git_operations.git_helper.cmd.Git")
    def test_default_validation_service_permission_denied(
        self, mock_git_cmd, git_settings
    ):
        """Test that DefaultGitValidationService handles permission denied errors correctly."""
        # Given
        service = DefaultGitValidationService()
        mock_git = MagicMock()
        mock_git.execute.side_effect = git.exc.GitCommandError(
            "git ls-remote", 128, "stderr: Permission denied"
        )
        mock_git_cmd.return_value = mock_git

        # When/Then
        with pytest.raises(GitValidationError) as exc_info:
            service.validate_repository_access(
                git_settings.repository_url, git_settings.access_token
            )

        # Verify error details
        error = exc_info.value
        assert error.error_type == "permission_denied"
        assert "Permission denied" in error.message
        assert error.status_code == 403


class TestGitHelperErrorHandling:
    """Tests for the error handling in GitHelper."""

    def test_convert_git_exception_to_validation_error(self):
        """Test the convert_git_exception_to_validation_error static method."""
        # Given
        git_exception = git.exc.GitCommandError(
            "git clone", 128, "stderr: Authentication failed"
        )

        # When
        error = GitHelper.convert_git_exception_to_validation_error(git_exception)

        # Then
        assert isinstance(error, GitValidationError)
        assert error.error_type == "authentication_failed"
        assert error.status_code == 401

    @patch("issue_solver.git_operations.git_helper.Repo")
    def test_clone_repository_success(self, mock_repo_class, git_settings):
        """Test successful repository cloning."""
        # Given
        mock_repo = Mock()
        mock_repo.active_branch.name = "main"
        mock_repo.head.commit.hexsha = "abc123"
        mock_repo_class.clone_from.return_value = mock_repo

        git_helper = GitHelper(git_settings)

        # When
        result = git_helper.clone_repository(Path("/tmp/repo"))

        # Then
        assert isinstance(result, CodeVersion)
        assert result.branch == "main"
        assert result.commit_sha == "abc123"
        mock_repo_class.clone_from.assert_called_once()

    @patch("issue_solver.git_operations.git_helper.Repo")
    def test_clone_repository_error_handling(self, mock_repo_class, git_settings):
        """Test error handling during repository cloning."""
        # Given
        mock_repo_class.clone_from.side_effect = git.exc.GitCommandError(
            "git clone", 128, "stderr: Repository not found"
        )

        git_helper = GitHelper(git_settings)

        # When/Then
        with pytest.raises(GitValidationError) as exc_info:
            git_helper.clone_repository(Path("/tmp/repo"))

        # Verify error details
        error = exc_info.value
        assert error.error_type == "repository_not_found"
        assert error.status_code == 404

    @patch("issue_solver.git_operations.git_helper.Repo")
    def test_pull_repository_error_handling(self, mock_repo_class, git_settings):
        """Test error handling during repository pulling."""
        # Given
        mock_repo = Mock()
        mock_repo.git.pull.side_effect = git.exc.GitCommandError(
            "git pull", 128, "stderr: Permission denied"
        )
        mock_repo_class.return_value = mock_repo

        git_helper = GitHelper(git_settings)

        # When/Then
        with pytest.raises(GitValidationError) as exc_info:
            git_helper.pull_repository(Path("/tmp/repo"))

        # Verify error details
        error = exc_info.value
        assert error.error_type == "permission_denied"
        assert error.status_code == 403

    def test_validation_service_injection(self, git_settings):
        """Test that manually injecting a validation service works."""
        # Given
        mock_validation_service = Mock(spec=NoopGitValidationService)

        # When
        git_helper = GitHelper(git_settings, validation_service=mock_validation_service)

        # Then
        assert git_helper.validation_service == mock_validation_service
