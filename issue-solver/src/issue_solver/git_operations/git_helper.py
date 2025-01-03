from pathlib import Path
from typing import Self

from pydantic import Field
from pydantic_settings import BaseSettings

from issue_solver.models.model_settings import ModelSettings


class GitHelper:
    def __init__(self, settings: "GitSettings") -> None:
        super().__init__()
        self.settings = settings

    @classmethod
    def of(cls, git_settings: "GitSettings", model_settings: ModelSettings) -> Self:
        return cls(git_settings)

    def commit_and_push(self, issue_description: str, repo_path: Path) -> None:
        pass


class GitSettings(BaseSettings):
    coding_agent_access_token: str | None = Field(
        default=None,
        description="Token used for CI/CD runner to push changes to the repository.",
    )
    agent_git_user_mail: str | None = Field(
        default=None,
        description="Email address used for Git commits.",
    )
    agent_git_user_name: str | None = Field(
        default=None,
        description="Username used for Git commits.",
    )
