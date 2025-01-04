from pydantic import Field, AnyUrl

from issue_solver.issue_trackers.settings import ApiBasedIssueTrackerSettings


class JiraIssueTrackerSettings(ApiBasedIssueTrackerSettings):
    base_url: AnyUrl = Field(
        description="Base URL for the Jira.",
        default="https://jira.atlassian.com",
    )
    project_id: str = Field(description="ID of the project in the issue tracker.")

    class Config:
        env_prefix = "JIRA_"
        env_file = ".env"
        env_file_encoding = "utf-8"
