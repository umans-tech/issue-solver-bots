import os

from issue_solver.git_operations.git_helper import (
    GitHubTokenPermissions,
    GitValidationError,
    GitValidationService,
    ValidationResult,
)

CURR_PATH = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT_PATH = os.path.join(CURR_PATH, "..")
ALEMBIC_INI_LOCATION = os.path.join(PROJECT_ROOT_PATH, "alembic.ini")
MIGRATIONS_PATH = os.path.join(
    PROJECT_ROOT_PATH, "src/issue_solver/database/migrations"
)


class NoopGitValidationService(GitValidationService):
    def __init__(self) -> None:
        self.inaccessible_repositories: dict[str, tuple[str, int]] = {}
        self.mocked_token_scopes: dict[tuple[str, str], list[str]] = {}

    def add_inaccessible_repository(
        self, url: str, error_type: str, status_code: int
    ) -> None:
        self.inaccessible_repositories[url] = (error_type, status_code)

    def mock_github_token_scopes(
        self, url: str, access_token: str, scopes: list[str]
    ) -> None:
        """Mock GitHub token scopes for testing"""
        self.mocked_token_scopes[(url, access_token)] = scopes

    def validate_repository_access(
        self, url: str, access_token: str
    ) -> ValidationResult:
        if url in self.inaccessible_repositories:
            error_type, status_code = self.inaccessible_repositories[url]
            raise GitValidationError(
                f"Validation failed for repository: {url} - {error_type}",
                "validation_failed",
                status_code,
            )

        # Check if we have mocked token scopes for this URL and token
        token_permissions = None
        if (url, access_token) in self.mocked_token_scopes:
            scopes = self.mocked_token_scopes[(url, access_token)]
            token_permissions = GitHubTokenPermissions(scopes=scopes)

        return ValidationResult(success=True, token_permissions=token_permissions)
