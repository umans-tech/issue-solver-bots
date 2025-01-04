from enum import StrEnum

from pydantic import AnyUrl, Field

from issue_solver.issue_trackers.settings import ApiBasedIssueTrackerSettings


class GitlabObjectType(StrEnum):
    ISSUE = "ISSUE"
    MR = "MR"


class GitlabIssueTrackerSettings(ApiBasedIssueTrackerSettings):
    base_url: AnyUrl = Field(
        description="Base URL for the GitLab.",
        default="https://gitlab.com",
    )
    project_id: str | None = Field(
        description="ID of the project in the issue tracker."
    )
    object_type: GitlabObjectType = Field(
        default=GitlabObjectType.ISSUE,
        description="Determines whether we retrieve from an ISSUE or a MR in GitLab.",
    )

    class Config:
        env_prefix = "GITLAB_"
        env_file = ".env"
        env_file_encoding = "utf-8"
