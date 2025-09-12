import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from shutil import rmtree
from typing import Any, Callable, Optional, Self, TypeVar, cast

import git
from git import Repo, cmd
from github import Github
from gitlab import Gitlab
import httpx

from issue_solver.issues.issue import IssueInfo
from issue_solver.models.model_settings import ModelSettings
from pydantic import Field
from pydantic_settings import BaseSettings


@dataclass
class GitValidationError(Exception):
    message: str
    error_type: str
    status_code: int

    def __init__(self, message: str, error_type: str, status_code: int = 500):
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        super().__init__(message)


@dataclass
class GitHubTokenPermissions:
    """Represents GitHub token permissions and validation status"""

    scopes: list[str]
    has_repo: bool = False
    has_workflow: bool = False
    has_read_user: bool = False
    missing_scopes: list[str] = field(default_factory=list)

    def __post_init__(self):
        # Check for required permissions
        self.has_repo = "repo" in self.scopes
        self.has_workflow = "workflow" in self.scopes
        self.has_read_user = "read:user" in self.scopes or "user" in self.scopes

        # Calculate missing scopes
        self.missing_scopes = []

        if not self.has_repo:
            self.missing_scopes.append("repo")
        if not self.has_workflow:
            self.missing_scopes.append("workflow")
        if not self.has_read_user:
            self.missing_scopes.append("read:user")

    @property
    def is_optimal(self) -> bool:
        """Returns True if all required scopes are present"""
        return len(self.missing_scopes) == 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to a dictionary for serialization"""
        return {
            "scopes": self.scopes,
            "has_repo": self.has_repo,
            "has_workflow": self.has_workflow,
            "has_read_user": self.has_read_user,
            "missing_scopes": self.missing_scopes,
            "is_optimal": self.is_optimal,
        }


@dataclass
class ValidationResult:
    """Result of repository validation including optional token permissions"""

    success: bool
    token_permissions: GitHubTokenPermissions | None = None


class GitValidationService(ABC):
    @abstractmethod
    def validate_repository_access(
        self, url: str, access_token: str
    ) -> ValidationResult:
        pass


class DefaultGitValidationService(GitValidationService):
    def validate_repository_access(
        self, url: str, access_token: str
    ) -> ValidationResult:
        # First validate repository access (existing logic)
        self._validate_git_access(url, access_token)

        # Then optionally fetch token permissions for GitHub repos
        token_permissions = None
        if access_token and self._is_github_repo(url):
            try:
                token_permissions = self._fetch_github_token_scopes(access_token)
            except Exception:
                # Don't fail validation if we can't fetch scopes, just log it
                # This maintains backwards compatibility
                pass

        return ValidationResult(success=True, token_permissions=token_permissions)

    def _validate_git_access(self, url: str, access_token: str) -> None:
        """Original validation logic - unchanged"""
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

    def _is_github_repo(self, url: str) -> bool:
        """Check if the repository URL is a GitHub repository"""
        return "github.com" in url.lower()

    def _fetch_github_token_scopes(self, access_token: str) -> GitHubTokenPermissions:
        """Fetch GitHub token scopes using the GitHub API"""
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        # Use the GitHub API to check token scopes
        with httpx.Client() as client:
            response = client.get("https://api.github.com/user", headers=headers)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch token info: {response.status_code}")

        # Extract scopes from the response headers
        scopes_header = response.headers.get("X-OAuth-Scopes", "")
        scopes = [scope.strip() for scope in scopes_header.split(",") if scope.strip()]

        return GitHubTokenPermissions(scopes=scopes)


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

    def validate_repository_access(self) -> ValidationResult:
        return self.validation_service.validate_repository_access(
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
            commit_message = f"feat: automated resolution of '{issue_info.title}' (automated change 🤖✨)"
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
        default="agent@umans.ai",
        description="Email address used for Git commits.",
    )
    user_name: str = Field(
        default="umans-agent",
        description="Username used for Git commits.",
    )


@dataclass
class PullRequestReference:
    url: str
    number: int


class GitClient:
    @staticmethod
    def _default_branch(
        remote_url: str, access_token: str | None, repo_path: Path | None = None
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
        access_token: str | None,
        to_path: Path,
        new_branch_name: str | None = None,
    ) -> None:
        GitHelper(
            settings=GitSettings(repository_url=url, access_token=access_token)
        ).clone_repository(to_path=to_path, new_branch_name=new_branch_name)

    @classmethod
    def commit_and_submit_pr(
        cls,
        access_token,
        git_repository_url,
        issue_info,
        process_id,
        repo_path,
    ):
        cls.commit_and_push(
            issue_info=issue_info,
            repo_path=repo_path,
            url=git_repository_url,
            access_token=access_token,
        )
        pr_reference = cls.submit_pull_request(
            repo_path=repo_path,
            title=issue_info.title or f"automatic issue resolution {process_id}",
            body=issue_info.description,
            access_token=access_token,
            url=git_repository_url,
        )
        return pr_reference

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
    def clone_repo_and_branch(
        cls,
        process_id: str,
        repo_path: Path,
        url: str,
        access_token: str | None,
        issue: IssueInfo | None = None,
    ) -> None:
        if repo_path.exists():
            rmtree(repo_path)
        new_branch_name = (
            name_new_branch_for_issue(issue, process_id)
            if issue
            else cls._default_branch(url, access_token, repo_path)
        )
        cls.clone_repository(
            url=url,
            access_token=access_token,
            to_path=repo_path,
            new_branch_name=new_branch_name,
        )

    @classmethod
    def submit_pull_request(
        cls,
        repo_path: Path,
        title: str,
        body: str,
        access_token: str,
        url: str | None = None,
        branch: str | None = None,
    ) -> PullRequestReference:
        repo = Repo(repo_path)
        source_branch = branch or repo.active_branch.name
        remote_url = url or repo.remotes.origin.url
        target_branch = cls._default_branch(remote_url, access_token, repo_path)

        if "github.com" in remote_url.lower():
            return cls._submit_github_pr(
                access_token, body, remote_url, source_branch, target_branch, title
            )
        elif "gitlab.com" in remote_url.lower():
            return cls._submit_gitlab_mr(
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
    ) -> PullRequestReference:
        owner_repo = remote_url.removesuffix(".git").replace("https://gitlab.com/", "")
        gl = Gitlab("https://gitlab.com", private_token=access_token)
        mr = gl.projects.get(owner_repo).mergerequests.create(
            {
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title,
                "description": body,
            }
        )
        return PullRequestReference(
            url=f"https://gitlab.com/{owner_repo}/merge_requests/{mr.iid}",
            number=mr.iid,
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
    ) -> PullRequestReference:
        owner_repo = remote_url.removesuffix(".git").replace("https://github.com/", "")
        pr = (
            Github(access_token)
            .get_repo(owner_repo)
            .create_pull(title=title, body=body, head=source_branch, base=target_branch)
        )
        return PullRequestReference(
            url=f"https://github.com/{owner_repo}/pull/{pr.number}",
            number=pr.number,
        )

    @classmethod
    def switch_to_issue_branch(
        cls,
        process_id: str,
        repo_path: Path,
        issue: IssueInfo,
    ) -> None:
        new_branch_name = name_new_branch_for_issue(issue, process_id)
        repo = Repo(repo_path)
        if repo.is_dirty(untracked_files=True):
            repo.git.stash(
                "push", "-m", f"auto-stash-before-switching-to-{new_branch_name}"
            )
        if new_branch_name in repo.branches:
            repo.git.checkout(new_branch_name)
        else:
            repo.git.checkout("-b", new_branch_name)


def name_new_branch_for_issue(issue: IssueInfo, process_id: str) -> str:
    title_part = sanitize_branch_name(issue.title or "resolution")
    new_branch_name = f"auto/{process_id}/{title_part}"
    return new_branch_name


def sanitize_branch_name(name: str) -> str:
    """Sanitize a string to be a valid Git branch name.

    Git branch names cannot contain:
    - Spaces, ~, ^, :, ?, *, [, ]
    - Start or end with /, ., or -
    - Contain consecutive dots ..
    - End with .lock
    - Contain @{
    - Be empty or contain only whitespace
    """
    if not name or not name.strip():
        return "resolution"

    # Replace invalid characters with hyphens
    sanitized = re.sub(r"[^a-zA-Z0-9._-]", "-", name.strip())

    # Remove consecutive hyphens/dots/underscores
    sanitized = re.sub(r"[-_.]{2,}", "-", sanitized)

    # Remove leading/trailing invalid characters
    sanitized = sanitized.strip("-._")

    # Ensure it's not empty after sanitization
    if not sanitized:
        return "resolution"

    # Truncate to reasonable length and ensure it doesn't end with invalid chars
    return sanitized[:50].rstrip("-._")


def extract_git_clone_default_directory_name(repo_url: str) -> str:
    url = repo_url.rstrip("/")

    if ":" in url and not url.startswith("http"):
        url = url.split(":", 1)[-1]  # Get everything after first colon

    if url.endswith(".git"):
        url = url[:-4]

    url = url.rstrip("/")

    if "/" in url:
        directory_name = url.split("/")[-1]
    else:
        directory_name = url

    return directory_name
