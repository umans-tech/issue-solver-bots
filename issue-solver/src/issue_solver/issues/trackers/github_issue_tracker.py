from enum import StrEnum
from typing import Literal

from pydantic import AnyUrl, Field
from pydantic_core import Url
from pydantic_settings import SettingsConfigDict

from issue_solver.issues.trackers.issue_tracker import (
    IssueTracker,
    IssueInfo,
    IssueReference,
)
from issue_solver.issues.settings import ApiBasedIssueTrackerSettings


class GithubObjectType(StrEnum):
    ISSUE = "ISSUE"
    MR = "MR"


class GithubIssueTracker(IssueTracker):
    def describe_issue(self, issue_reference: IssueReference) -> IssueInfo | None:
        raise NotImplementedError(
            "GithubIssueTracker.get_issue_description is not implemented"
        )

    class Settings(ApiBasedIssueTrackerSettings):
        type: Literal["GITHUB"] = "GITHUB"
        base_url: AnyUrl = Field(
            description="Base URL for the GitHub.",
            default=Url("https://api.github.com"),
        )
        object_type: GithubObjectType = Field(
            default=GithubObjectType.ISSUE,
            description="Determines whether we retrieve from an ISSUE or a MR in GitLab.",
        )

        model_config = SettingsConfigDict(
            env_prefix="GITHUB_", env_file=".env", env_file_encoding="utf-8"
        )
