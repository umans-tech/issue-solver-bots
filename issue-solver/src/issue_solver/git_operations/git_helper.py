from pathlib import Path
from typing import Self

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
        pass


class GitSettings(BaseSettings):
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
