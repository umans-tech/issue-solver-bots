from enum import StrEnum

from pydantic import Field, AnyUrl
from pydantic_core import Url
from pydantic_settings import SettingsConfigDict

from issue_solver.issue_trackers.settings import ApiBasedIssueTrackerSettings


class GithubObjectType(StrEnum):
    ISSUE = "ISSUE"
    MR = "MR"


class GithubIssueTrackerSettings(ApiBasedIssueTrackerSettings):
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
