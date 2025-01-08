from abc import ABC

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiBasedIssueTrackerSettings(BaseSettings, ABC):
    base_url: AnyUrl = Field(description="Base URL for the issue tracker.")
    private_token: str | None = Field(
        description="Private token for the issue tracker.", default=None
    )
    api_version: str | None = Field(
        description="API version for the issue tracker.", default=None
    )

    model_config = SettingsConfigDict(extra="ignore")
