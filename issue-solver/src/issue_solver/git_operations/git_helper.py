from dataclasses import dataclass
from pathlib import Path
from typing import Self

from git import Repo
from issue_solver.issues.issue import IssueInfo
from issue_solver.models.model_settings import ModelSettings
from pydantic import Field
from pydantic_settings import BaseSettings


class GitHelper:
    def __init__(self, settings: "GitSettings") -> None:
        super().__init__()
        self.settings = settings

    @classmethod
    def of(
        cls, git_settings: "GitSettings", model_settings: ModelSettings | None = None
    ) -> Self:
        return cls(git_settings)

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

    def clone_repository(self, to_path: Path) -> "CodeVersion":
        """
        Clone the repository to the current working directory.
        """
        repo = Repo.clone_from(
            self.settings.repository_url,
            to_path=to_path,
            env={"GIT_TERMINAL_PROMPT": "0"},
            depth=1,
        )
        # return branch name and commit sha
        return CodeVersion(
            branch=repo.active_branch.name, commit_sha=repo.head.commit.hexsha
        )


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
