from pydantic import Field, AnyUrl
from pydantic_core import Url
from pydantic_settings import SettingsConfigDict

from issue_solver.issue_trackers.settings import ApiBasedIssueTrackerSettings


class TrelloIssueTrackerSettings(ApiBasedIssueTrackerSettings):
    base_url: AnyUrl = Field(
        description="Base URL for the Trello.",
        default=Url("https://api.trello.com"),
    )
    api_version: str = Field(
        description="API version for the Trello.",
        default="1",
    )

    board_id: str = Field(description="ID of the board in the issue tracker.")

    model_config = SettingsConfigDict(
        env_prefix="TRELLO_",
        env_file=".env",
        env_file_encoding="utf-8",
    )
