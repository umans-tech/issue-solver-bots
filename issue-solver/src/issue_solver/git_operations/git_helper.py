from pathlib import Path
from typing import Self

from git import Repo
from pydantic import Field
from pydantic_settings import BaseSettings

from issue_solver.issues.issue import IssueInfo
from issue_solver.models.model_settings import ModelSettings


class GitHelper:
    def __init__(self, settings: "GitSettings") -> None:
        super().__init__()
        self.settings = settings

    @classmethod
    def of(cls, git_settings: "GitSettings", model_settings: ModelSettings) -> Self:
        return cls(git_settings)

    def commit_and_push(self, issue_description: IssueInfo, repo_path: Path) -> None:
        repo = Repo(path=repo_path)
        repo.git.config("user.email", self.settings.user_mail)
        repo.git.config("user.name", self.settings.user_name)
        if self.settings.repository_url:
            repo.git.remote(
                "add",
                "repo_origin",
                f"https://oauth2:{self.settings.access_token}@{self.settings.repository_url.lstrip('https://')}",
            )
        repo.git.add(".")
        repo.index.commit(
            f"automated resolution of {issue_description.title} (automated change 🤖✨)"
        )
        repo.git.push("repo_origin", f"HEAD:{repo.active_branch.name}")


class GitSettings(BaseSettings):
    repository_url: str | None = Field(
        description="URL of the repository where the changes are pushed.",
        default=None,
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
