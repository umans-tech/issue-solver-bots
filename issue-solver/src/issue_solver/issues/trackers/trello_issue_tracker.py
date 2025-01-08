from typing import Literal

from pydantic import AnyUrl, Field
from pydantic_core import Url
from pydantic_settings import SettingsConfigDict

from issue_solver.issues.issue import IssueReference, IssueInfo
from issue_solver.issues.trackers.issue_tracker import (
    IssueTracker,
)
from issue_solver.issues.trackers.settings import ApiBasedIssueTrackerSettings


class TrelloIssueTracker(IssueTracker):
    def describe_issue(self, issue_reference: IssueReference) -> IssueInfo | None:
        raise NotImplementedError(
            "TrelloIssueTracker.get_issue_description is not implemented"
        )

    class Settings(ApiBasedIssueTrackerSettings):
        type: Literal["TRELLO"] = "TRELLO"
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
