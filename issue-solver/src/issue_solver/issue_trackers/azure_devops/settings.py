from pydantic import Field, AnyUrl

from issue_solver.issue_trackers.settings import ApiBasedIssueTrackerSettings


class AzureDevOpsIssueTrackerSettings(ApiBasedIssueTrackerSettings):
    base_url: AnyUrl = Field(
        description="Base URL for the Azure DevOps.",
        default="https://dev.azure.com",
    )
    project_id: str = Field(description="ID of the project in the issue tracker.")

    class Config:
        env_prefix = "AZURE_DEVOPS_"
        env_file = ".env"
        env_file_encoding = "utf-8"
