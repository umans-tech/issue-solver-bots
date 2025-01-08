from typing import Literal

from pydantic import Field, AnyUrl
from pydantic_core import Url
from pydantic_settings import SettingsConfigDict

from issue_solver.issue_trackers.settings import ApiBasedIssueTrackerSettings


class JiraIssueTrackerSettings(ApiBasedIssueTrackerSettings):
    type: Literal["JIRA"] = "JIRA"
    base_url: AnyUrl = Field(
        description="Base URL for the Jira.",
        default=Url("https://jira.atlassian.com"),
    )
    project_id: str = Field(description="ID of the project in the issue tracker.")

    model_config = SettingsConfigDict(
        env_prefix="JIRA_",
        env_file=".env",
        env_file_encoding="utf-8",
    )
