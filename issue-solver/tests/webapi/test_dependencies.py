from unittest.mock import patch
import os

from issue_solver.webapi.dependencies import (
    get_validation_service,
    get_git_validation_service,
    get_noop_git_validation_service,
    NoopGitValidationService,
    DefaultGitValidationService,
)


class TestDependencies:
    """Tests for dependency injection functions in the webapi."""

    def test_get_git_validation_service(self):
        """Test that get_git_validation_service returns a DefaultGitValidationService."""
        # When
        service = get_git_validation_service()

        # Then
        assert isinstance(service, DefaultGitValidationService)

    def test_get_noop_validation_service(self):
        """Test that get_noop_git_validation_service returns a NoopGitValidationService."""
        # When
        service = get_noop_git_validation_service()

        # Then
        assert isinstance(service, NoopGitValidationService)

    @patch.dict(os.environ, {"TESTING": "true"})
    def test_get_validation_service_testing_mode(self):
        """Test that get_validation_service returns NoopGitValidationService in testing mode."""
        # When
        service = get_validation_service()

        # Then
        assert isinstance(service, NoopGitValidationService)

    @patch.dict(os.environ, {"TESTING": ""})
    def test_get_validation_service_production_mode(self):
        """Test that get_validation_service returns DefaultGitValidationService in production mode."""
        # When
        service = get_validation_service()

        # Then
        assert isinstance(service, DefaultGitValidationService)

    @patch.dict(os.environ, {})
    def test_get_validation_service_no_env_var(self):
        """Test that get_validation_service returns DefaultGitValidationService when TESTING is not set."""
        # When
        service = get_validation_service()

        # Then
        assert isinstance(service, DefaultGitValidationService)
