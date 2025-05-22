from typing import Literal

from pydantic import AnyUrl, Field
from pydantic_settings import SettingsConfigDict

from issue_solver.issues.issue import IssueReference, IssueInfo
from issue_solver.issues.trackers.issue_tracker import (
    IssueTracker,
)
from issue_solver.issues.trackers.settings import ApiBasedIssueTrackerSettings


class AzureDevOpsIssueTracker(IssueTracker):
    def describe_issue(self, issue_reference: IssueReference) -> IssueInfo | None:
        raise NotImplementedError(
            "AzureDevOpsIssueTracker.get_issue_description is not implemented"
        )

    class Settings(ApiBasedIssueTrackerSettings):
        type: Literal["AZURE_DEVOPS"] = "AZURE_DEVOPS"
        base_url: AnyUrl = Field(
            description="Base URL for the Azure DevOps.",
            default=AnyUrl("https://dev.azure.com"),
        )

        model_config = SettingsConfigDict(
            env_prefix="AZURE_DEVOPS_",
            env_file=".env",
            env_file_encoding="utf-8",
        )
