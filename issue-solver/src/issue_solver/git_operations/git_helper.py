from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional, Self, TypeVar, cast

import git
from git import Repo, cmd
from github import Github
from gitlab import Gitlab

from issue_solver.issues.issue import IssueInfo
from issue_solver.models.model_settings import ModelSettings
from pydantic import Field
from pydantic_settings import BaseSettings


class GitValidationError(Exception):
    def __init__(self, message: str, error_type: str, status_code: int = 500):
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        super().__init__(message)


class GitValidationService(ABC):
    @abstractmethod
    def validate_repository_access(self, url: str, access_token: str) -> None:
        pass


class DefaultGitValidationService(GitValidationService):
    def validate_repository_access(self, url: str, access_token: str) -> None:
        try:
            stripped_url = url.removeprefix("https://")
            auth_url = (
                f"https://oauth2:{access_token}@{stripped_url}"
                if access_token
                else f"https://{stripped_url}"
            )

            repo = cmd.Git()
            repo.execute(["git", "ls-remote", "--quiet", auth_url])

        except git.exc.GitCommandError as e:
            error_message = str(e)

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
            raise GitValidationError(
                f"Unexpected error validating repository: {str(e)}",
                "unexpected_error",
                500,
            )


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
    ) -> GitValidationError:
        error_message = str(exception)

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
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(self, *args, **kwargs)
            except git.exc.GitCommandError as e:
                raise self.convert_git_exception_to_validation_error(e)
            except Exception as e:
                raise GitValidationError(
                    f"Unexpected error: {str(e)}", "unexpected_error", 500
                )

        return cast(
            Callable[..., T], wrapper
        )  # Cast to help mypy understand the return type

    def validate_repository_access(self) -> None:
        self.validation_service.validate_repository_access(
            self.settings.repository_url, self.settings.access_token
        )

    def commit_and_push(self, issue_info: IssueInfo, repo_path: Path) -> None:
        repo = self._initialize_git_repo(repo_path)
        remote_url = self._resolve_remote_url(repo)

        if remote_url:
            authenticated_url = self._inject_access_token(remote_url)
            self._ensure_repo_origin(repo, authenticated_url)

        self._commit_changes(repo, issue_info)
        self._push_changes(repo)

    def _initialize_git_repo(self, repo_path: Path) -> Repo:
        repo = Repo(repo_path)
        repo.git.config("user.email", self.settings.user_mail)
        repo.git.config("user.name", self.settings.user_name)
        return repo

    def _resolve_remote_url(self, repo: Repo) -> str | None:
        if self.settings.repository_url:
            return self.settings.repository_url

        if "origin" in repo.remotes:
            return repo.remotes.origin.url

        return None

    def _inject_access_token(self, base_url: str) -> str:
        stripped_url = base_url.removeprefix("https://")
        if self.settings.access_token:
            return f"https://oauth2:{self.settings.access_token}@{stripped_url}"
        return f"https://{stripped_url}"

    def _ensure_repo_origin(self, repo: Repo, url: str) -> None:
        if "repo_origin" not in repo.remotes:
            repo.git.remote("add", "repo_origin", url)
        else:
            repo.git.remote("set-url", "repo_origin", url)

    def _commit_changes(self, repo: Repo, issue_info: IssueInfo) -> None:
        repo.git.add(A=True)  # Equivalent to `git add --all`
        if repo.is_dirty(untracked_files=True):
            commit_message = (
                f"Automated resolution of '{issue_info.title}' "
                "(automated change 🤖✨)"
            )
            repo.index.commit(commit_message)

    def _push_changes(self, repo: Repo) -> None:
        if "repo_origin" in repo.remotes:
            branch_name = repo.active_branch.name
            repo.git.push("repo_origin", f"HEAD:{branch_name}")
        else:
            print("No 'repo_origin' remote found. Cannot push changes.")

    def clone_repository(
        self, to_path: Path, depth: int | None = 1, new_branch_name=None
    ) -> "CodeVersion":
        try:
            repo = Repo.clone_from(
                self._inject_access_token(self.settings.repository_url),
                to_path=to_path,
                env={"GIT_TERMINAL_PROMPT": "0"},
                depth=depth,
            )
            if new_branch_name:
                repo.git.checkout(new_branch_name, b=True)
            code_version = CodeVersion(
                branch=repo.active_branch.name, commit_sha=repo.head.commit.hexsha
            )
            return code_version
        except git.exc.GitCommandError as e:
            raise self.convert_git_exception_to_validation_error(e)

    def pull_repository(
        self,
        repo_path: Path,
    ) -> "CodeVersion":
        try:
            repo = Repo(repo_path)
            repo.git.pull()
            return CodeVersion(
                branch=repo.active_branch.name, commit_sha=repo.head.commit.hexsha
            )
        except git.exc.GitCommandError as e:
            raise self.convert_git_exception_to_validation_error(e)

    def get_changed_files_commit(
        self,
        repo_path: Path,
        last_indexed_commit_sha: str,
    ) -> GitDiffFiles:
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
            raise self.convert_git_exception_to_validation_error(e)


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


class GitClient:
    @staticmethod
    def _default_branch(
        remote_url: str, access_token: str, repo_path: Path | None = None
    ) -> str:
        url = remote_url.removesuffix(".git")
        if "github.com" in url.lower():
            owner_repo = url.replace("https://github.com/", "")
            return Github(access_token).get_repo(owner_repo).default_branch
        if "gitlab.com" in url.lower():
            owner_repo = url.replace("https://gitlab.com/", "")
            return (
                Gitlab("https://gitlab.com", private_token=access_token)
                .projects.get(owner_repo)
                .default_branch
            )
        if repo_path:
            head_ref = Repo(repo_path).git.symbolic_ref("refs/remotes/origin/HEAD")
            return head_ref.split("/")[-1]
        return "main"

    @classmethod
    def clone_repository(
        cls,
        url: str,
        access_token: str,
        to_path: Path,
        new_branch_name: str | None = None,
    ) -> None:
        GitHelper(
            settings=GitSettings(repository_url=url, access_token=access_token)
        ).clone_repository(to_path=to_path, new_branch_name=new_branch_name)

    @classmethod
    def commit_and_push(
        cls,
        issue_info: IssueInfo,
        repo_path: Path,
        url: str,
        access_token: str,
    ) -> None:
        GitHelper(
            settings=GitSettings(repository_url=url, access_token=access_token)
        ).commit_and_push(issue_info, repo_path)

    @classmethod
    def submit_pull_request(
        cls,
        repo_path: Path,
        title: str,
        body: str,
        access_token: str,
        url: str | None = None,
        branch: str | None = None,
    ) -> None:
        repo = Repo(repo_path)
        source_branch = branch or repo.active_branch.name
        remote_url = url or repo.remotes.origin.url
        target_branch = cls._default_branch(remote_url, access_token, repo_path)

        if "github.com" in remote_url.lower():
            cls._submit_github_pr(
                access_token, body, remote_url, source_branch, target_branch, title
            )
        elif "gitlab.com" in remote_url.lower():
            cls._submit_gitlab_mr(
                access_token, body, remote_url, source_branch, target_branch, title
            )
        else:
            raise GitValidationError(
                f"Unsupported Git service: {remote_url}", "unsupported_git_service", 400
            )

    @classmethod
    def _submit_gitlab_mr(
        cls,
        access_token: str,
        body: str,
        remote_url: str,
        source_branch: str,
        target_branch: str,
        title: str,
    ) -> None:
        owner_repo = remote_url.removesuffix(".git").replace("https://gitlab.com/", "")
        gl = Gitlab("https://gitlab.com", private_token=access_token)
        gl.projects.get(owner_repo).mergerequests.create(
            {
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title,
                "description": body,
            }
        )

    @classmethod
    def _submit_github_pr(
        cls,
        access_token: str,
        body: str,
        remote_url: str,
        source_branch: str,
        target_branch: str,
        title: str,
    ) -> None:
        owner_repo = remote_url.removesuffix(".git").replace("https://github.com/", "")
        Github(access_token).get_repo(owner_repo).create_pull(
            title=title, body=body, head=source_branch, base=target_branch
        )
