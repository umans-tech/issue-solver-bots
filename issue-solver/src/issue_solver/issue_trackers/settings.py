from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiBasedIssueTrackerSettings(BaseSettings):
    base_url: AnyUrl = Field(description="Base URL for the issue tracker.")
    private_token: str = Field(description="Private token for the issue tracker.")
    api_version: str = Field(description="API version for the issue tracker.")

    model_config = SettingsConfigDict(extra="ignore")
