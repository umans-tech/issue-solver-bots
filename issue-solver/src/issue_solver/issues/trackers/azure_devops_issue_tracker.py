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


class AzureDevOpsIssueTracker(IssueTracker):
    def describe_issue(self, issue_reference: IssueReference) -> IssueInfo | None:
        raise NotImplementedError(
            "AzureDevOpsIssueTracker.get_issue_description is not implemented"
        )

    class Settings(ApiBasedIssueTrackerSettings):
        type: Literal["AZURE"] = "AZURE"
        base_url: AnyUrl = Field(
            description="Base URL for the Azure DevOps.",
            default=Url("https://dev.azure.com"),
        )
        project_id: str = Field(description="ID of the project in the issue tracker.")

        model_config = SettingsConfigDict(
            env_prefix="AZURE_DEVOPS_",
            env_file=".env",
            env_file_encoding="utf-8",
        )
