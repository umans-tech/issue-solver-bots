from typing import Literal

from pydantic import Field, AnyUrl
from pydantic_core import Url
from pydantic_settings import SettingsConfigDict

from issue_solver.issue_trackers.settings import ApiBasedIssueTrackerSettings


class AzureDevOpsIssueTrackerSettings(ApiBasedIssueTrackerSettings):
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
