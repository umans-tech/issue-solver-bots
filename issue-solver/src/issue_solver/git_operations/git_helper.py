from dataclasses import dataclass
from pathlib import Path
from typing import Self, Protocol, Optional, Any, Union, TypeVar, Callable, cast
import logging
from logging import LoggerAdapter
import git
from git import Repo, cmd
from issue_solver.issues.issue import IssueInfo
from issue_solver.models.model_settings import ModelSettings
from pydantic import Field
from pydantic_settings import BaseSettings


class GitValidationError(Exception):
    """Exception raised when repository validation fails."""

    def __init__(self, message: str, error_type: str, status_code: int = 500):
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        super().__init__(message)


class GitValidationService(Protocol):
    """Protocol for Git validation service."""

    def validate_repository_access(
        self,
        url: str,
        access_token: str,
        logger: Optional[Union[logging.Logger, LoggerAdapter[Any]]] = None,
    ) -> None:
        """
        Validate that a repository can be accessed with the given URL and access token.

        Args:
            url: Repository URL
            access_token: Access token for the repository
            logger: Optional logger for logging validation attempts

        Raises:
            GitValidationError: If the repository cannot be accessed
        """
        ...


class DefaultGitValidationService:
    """Default implementation of Git validation service."""

    def validate_repository_access(
        self,
        url: str,
        access_token: str,
        logger: Optional[Union[logging.Logger, LoggerAdapter[Any]]] = None,
    ) -> None:
        """
        Validate that a repository can be accessed with the given URL and access token.

        Args:
            url: Repository URL
            access_token: Access token for the repository
            logger: Optional logger for logging validation attempts

        Raises:
            GitValidationError: If the repository cannot be accessed
        """
        if logger:
            logger.info(f"Validating repository access: {url}")

        try:
            # Prepare the authenticated URL
            stripped_url = url.removeprefix("https://")
            auth_url = (
                f"https://oauth2:{access_token}@{stripped_url}"
                if access_token
                else f"https://{stripped_url}"
            )

            # Use git ls-remote which doesn't clone the repo but checks access
            repo = cmd.Git()
            repo.execute(["git", "ls-remote", "--quiet", auth_url])

            if logger:
                logger.info(f"Successfully validated repository access: {url}")
        except git.exc.GitCommandError as e:
            error_message = str(e)

            if logger:
                logger.error(f"Git command error: {error_message}")

            # Determine error type and status code based on error message
            if "Authentication failed" in error_message or "401" in error_message:
                raise GitValidationError(
                    "Authentication failed. Please check your access token.",
                    "authentication_failed",
                    401,
                )
            elif "not found" in error_message or "404" in error_message:
                raise GitValidationError(
                    "Repository not found. Please check the URL.",
                    "repository_not_found",
                    404,
                )
            elif (
                "could not resolve host" in error_message
                or "unable to access" in error_message
            ):
                raise GitValidationError(
                    "Could not access the repository. Please check the URL and your internet connection.",
                    "repository_unavailable",
                    502,
                )
            elif "Permission denied" in error_message or "403" in error_message:
                raise GitValidationError(
                    "Permission denied. Check your access rights to this repository.",
                    "permission_denied",
                    403,
                )
            else:
                raise GitValidationError(
                    f"Failed to access repository: {error_message}", "unknown", 500
                )
        except Exception as e:
            if logger:
                logger.error(f"Unexpected error validating repository: {str(e)}")
            raise GitValidationError(
                f"Unexpected error validating repository: {str(e)}",
                "unexpected_error",
                500,
            )


class NoopGitValidationService:
    """Validation service that performs no validation (for testing)."""

    def validate_repository_access(
        self,
        url: str,
        access_token: str,
        logger: Optional[Union[logging.Logger, LoggerAdapter[Any]]] = None,
    ) -> None:
        """No-op validation that always passes."""
        if logger:
            logger.info(f"NOOP validation for repository: {url}")


# Type variable for generic function return type
T = TypeVar("T")


@dataclass
class RenamedFile:
    old_file_name: Path
    new_file_name: Path


@dataclass
class GitDiffFiles:
    repo_path: Path
    added_files: list[Path]
    deleted_files: list[Path]
    modified_files: list[Path]
    renamed_files: list[RenamedFile]

    def get_paths_of_all_new_files(self) -> list[str]:
        all_new_files = self.added_files + self.modified_files
        all_new_files += [
            renamed_file.new_file_name for renamed_file in self.renamed_files
        ]
        return [str(self.repo_path.joinpath(file)) for file in all_new_files]

    def get_paths_of_all_obsolete_files(self) -> list[str]:
        all_obsolete_files = self.deleted_files + self.modified_files
        all_obsolete_files += [
            renamed_file.old_file_name for renamed_file in self.renamed_files
        ]
        return [str(self.repo_path.joinpath(file)) for file in all_obsolete_files]


class GitHelper:
    def __init__(
        self,
        settings: "GitSettings",
        validation_service: Optional[GitValidationService] = None,
    ) -> None:
        self.settings = settings
        self.validation_service = validation_service or DefaultGitValidationService()

    @classmethod
    def of(
        cls,
        git_settings: "GitSettings",
        model_settings: ModelSettings | None = None,
        validation_service: Optional[GitValidationService] = None,
    ) -> Self:
        return cls(git_settings, validation_service)

    @staticmethod
    def convert_git_exception_to_validation_error(
        exception: git.exc.GitCommandError,
        logger: Optional[Union[logging.Logger, LoggerAdapter[Any]]] = None,
    ) -> GitValidationError:
        """
        Converts a git.exc.GitCommandError to a GitValidationError with appropriate error type and message.

        Args:
            exception: The GitCommandError to convert
            logger: Optional logger for logging errors

        Returns:
            A GitValidationError with appropriate error type and message
        """
        error_message = str(exception)

        if logger:
            logger.error(f"Git command error: {error_message}")

        # Determine error type and status code based on error message
        if "Authentication failed" in error_message or "401" in error_message:
            return GitValidationError(
                "Authentication failed. Please check your access token.",
                "authentication_failed",
                401,
            )
        elif "not found" in error_message or "404" in error_message:
            return GitValidationError(
                "Repository not found. Please check the URL.",
                "repository_not_found",
                404,
            )
        elif (
            "could not resolve host" in error_message
            or "unable to access" in error_message
        ):
            return GitValidationError(
                "Could not access the repository. Please check the URL and your internet connection.",
                "repository_unavailable",
                502,
            )
        elif "Permission denied" in error_message or "403" in error_message:
            return GitValidationError(
                "Permission denied. Check your access rights to this repository.",
                "permission_denied",
                403,
            )
        else:
            return GitValidationError(
                f"Failed to access repository: {error_message}", "unknown", 500
            )

    def handle_git_exceptions(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        A decorator method that handles git.exc.GitCommandError exceptions and converts them to GitValidationError

        Args:
            func: The function to wrap

        Returns:
            A wrapped function that handles git exceptions
        """

        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(self, *args, **kwargs)
            except git.exc.GitCommandError as e:
                # Extract logger from kwargs if available, otherwise use None
                logger = kwargs.get("logger", None)
                # Convert GitCommandError to GitValidationError
                raise self.convert_git_exception_to_validation_error(e, logger)
            except Exception as e:
                logger = kwargs.get("logger", None)
                if logger:
                    logger.error(f"Unexpected error in Git operation: {str(e)}")
                raise GitValidationError(
                    f"Unexpected error: {str(e)}", "unexpected_error", 500
                )

        return cast(
            Callable[..., T], wrapper
        )  # Cast to help mypy understand the return type

    def validate_repository_access(
        self, logger: Optional[Union[logging.Logger, LoggerAdapter[Any]]] = None
    ) -> None:
        """
        Validate that the repository can be accessed with the configured URL and token.

        Args:
            logger: Optional logger for logging validation attempts

        Raises:
            GitValidationError: If the repository cannot be accessed
        """
        self.validation_service.validate_repository_access(
            self.settings.repository_url, self.settings.access_token, logger
        )

    def commit_and_push(self, issue_info: IssueInfo, repo_path: Path) -> None:
        """Commit changes and push them to a remote repository."""

        repo = self._initialize_git_repo(repo_path)
        remote_url = self._resolve_remote_url(repo)

        if remote_url:
            authenticated_url = self._inject_access_token(remote_url)
            self._ensure_repo_origin(repo, authenticated_url)

        self._commit_changes(repo, issue_info)
        self._push_changes(repo)

    def _initialize_git_repo(self, repo_path: Path) -> Repo:
        """Initialize local git repo and set the configured user name/email."""
        repo = Repo(repo_path)
        repo.git.config("user.email", self.settings.user_mail)
        repo.git.config("user.name", self.settings.user_name)
        return repo

    def _resolve_remote_url(self, repo: Repo) -> str | None:
        """
        Return the `repository_url` from settings if present,
        otherwise try to fetch the URL from the 'origin' remote if it exists.
        """
        if self.settings.repository_url:
            return self.settings.repository_url

        if "origin" in repo.remotes:
            return repo.remotes.origin.url

        return None

    def _inject_access_token(self, base_url: str) -> str:
        """
        Insert the token into the URL if available, forming:
            https://oauth2:<token>@your.git.server/...
        Otherwise, ensure the URL has https://.
        """
        stripped_url = base_url.removeprefix("https://")
        if self.settings.access_token:
            return f"https://oauth2:{self.settings.access_token}@{stripped_url}"
        return f"https://{stripped_url}"

    def _ensure_repo_origin(self, repo: Repo, url: str) -> None:
        """
        Ensure the remote named 'repo_origin' exists and is set to the given URL.
        If it already exists, update its URL instead of adding it again.
        """
        if "repo_origin" not in repo.remotes:
            repo.git.remote("add", "repo_origin", url)
        else:
            repo.git.remote("set-url", "repo_origin", url)

    def _commit_changes(self, repo: Repo, issue_info: IssueInfo) -> None:
        """
        Stage all changes and commit only if there are actual modifications.
        """
        repo.git.add(A=True)  # Equivalent to `git add --all`
        if repo.is_dirty(untracked_files=True):
            commit_message = (
                f"Automated resolution of '{issue_info.title}' "
                "(automated change 🤖✨)"
            )
            repo.index.commit(commit_message)

    def _push_changes(self, repo: Repo) -> None:
        """
        Push changes to 'repo_origin' if it exists, otherwise warn the user.
        """
        if "repo_origin" in repo.remotes:
            branch_name = repo.active_branch.name
            repo.git.push("repo_origin", f"HEAD:{branch_name}")
        else:
            print("No 'repo_origin' remote found. Cannot push changes.")

    def clone_repository(
        self,
        to_path: Path,
        depth: int | None = 1,
        logger: Optional[Union[logging.Logger, LoggerAdapter[Any]]] = None,
    ) -> "CodeVersion":
        """
        Clone the repository to the current working directory.

        Args:
            to_path: Path where to clone the repository
            depth: Depth of history to clone, None for complete history
            logger: Optional logger for error handling

        Returns:
            CodeVersion with branch and commit SHA

        Raises:
            GitValidationError: If the repository cannot be cloned
        """
        try:
            repo = Repo.clone_from(
                self._inject_access_token(self.settings.repository_url),
                to_path=to_path,
                env={"GIT_TERMINAL_PROMPT": "0"},
                depth=depth,
            )
            return CodeVersion(
                branch=repo.active_branch.name, commit_sha=repo.head.commit.hexsha
            )
        except git.exc.GitCommandError as e:
            raise self.convert_git_exception_to_validation_error(e, logger)

    def pull_repository(
        self,
        repo_path: Path,
        logger: Optional[Union[logging.Logger, LoggerAdapter[Any]]] = None,
    ) -> "CodeVersion":
        """
        Pull changes from the remote repository.

        Args:
            repo_path: Path to the repository
            logger: Optional logger for error handling

        Returns:
            CodeVersion with branch and commit SHA

        Raises:
            GitValidationError: If the repository cannot be pulled
        """
        try:
            repo = Repo(repo_path)
            repo.git.pull()
            return CodeVersion(
                branch=repo.active_branch.name, commit_sha=repo.head.commit.hexsha
            )
        except git.exc.GitCommandError as e:
            raise self.convert_git_exception_to_validation_error(e, logger)

    def get_changed_files_commit(
        self,
        repo_path: Path,
        last_indexed_commit_sha: str,
        logger: Optional[Union[logging.Logger, LoggerAdapter[Any]]] = None,
    ) -> GitDiffFiles:
        """
        Get files changed between the last indexed commit and HEAD.

        Args:
            repo_path: Path to the repository
            last_indexed_commit_sha: SHA of the last indexed commit
            logger: Optional logger for error handling

        Returns:
            GitDiffFiles with files changed since the last indexed commit

        Raises:
            GitValidationError: If the repository cannot be accessed or the diff cannot be obtained
        """
        try:
            repo = Repo(repo_path)

            # Get added, deleted, and modified files by parsing the diff output
            added_files = []
            deleted_files = []
            modified_files = []
            renamed_files = []

            # Get the diff between commits
            diff_index = repo.git.diff(
                "--name-status", last_indexed_commit_sha, "HEAD"
            ).splitlines()

            for line in diff_index:
                if not line.strip():
                    continue

                parts = line.split("\t")
                status = parts[0]

                # A: addition of a file
                if status.startswith("A"):
                    added_files.append(Path(parts[1]))
                # D: deletion of a file
                elif status.startswith("D"):
                    deleted_files.append(Path(parts[1]))
                # M: modification of file content
                elif status.startswith("M"):
                    modified_files.append(Path(parts[1]))
                # R: renaming of a file
                elif status.startswith("R"):
                    renamed_files.append(
                        RenamedFile(
                            old_file_name=Path(parts[1]), new_file_name=Path(parts[2])
                        )
                    )

            return GitDiffFiles(
                repo_path=repo_path,
                added_files=added_files,
                deleted_files=deleted_files,
                modified_files=modified_files,
                renamed_files=renamed_files,
            )
        except git.exc.GitCommandError as e:
            raise self.convert_git_exception_to_validation_error(e, logger)


@dataclass
class CodeVersion:
    branch: str
    commit_sha: str


class GitSettings(BaseSettings):
    repository_url: str = Field(
        description="URL of the repository where the changes are pushed.",
        default="",
    )
    access_token: str = Field(
        description="Token used for CI/CD runner to push changes to the repository.",
    )
    user_mail: str = Field(
        default="ai.agent@umans.tech",
        description="Email address used for Git commits.",
    )
    user_name: str = Field(
        default="umans-agent",
        description="Username used for Git commits.",
    )
