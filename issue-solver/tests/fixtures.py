import logging
import os
from logging import LoggerAdapter
from typing import Any, Optional, Union

from issue_solver.git_operations.git_helper import (
    GitValidationError,
    GitValidationService,
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

    def add_inaccessible_repository(
        self, url: str, error_type: str, status_code: int
    ) -> None:
        self.inaccessible_repositories[url] = (error_type, status_code)

    def validate_repository_access(
        self,
        url: str,
        access_token: str,
        logger: Optional[Union[logging.Logger, LoggerAdapter[Any]]] = None,
    ) -> None:
        if url in self.inaccessible_repositories:
            error_type, status_code = self.inaccessible_repositories[url]
            raise GitValidationError(
                f"Validation failed for repository: {url} - {error_type}",
                "validation_failed",
                status_code,
            )
