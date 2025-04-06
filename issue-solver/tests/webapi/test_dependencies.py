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

    def test_get_validation_service_returns_default(self):
        """Test that get_validation_service always returns DefaultGitValidationService.

        In the updated architecture, we rely on dependency injection for testing
        rather than environment variables.
        """
        # When
        service = get_validation_service()

        # Then
        assert isinstance(service, DefaultGitValidationService)
