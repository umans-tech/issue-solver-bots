from typing import Literal

from pydantic_settings import SettingsConfigDict

from issue_solver.issues.issue import IssueReference, IssueInfo
from issue_solver.issues.trackers.issue_tracker import (
    IssueTracker,
)
from issue_solver.issues.trackers.settings import ApiBasedIssueTrackerSettings


class HttpBasedIssueTracker(IssueTracker):
    def describe_issue(self, issue_reference: IssueReference) -> IssueInfo | None:
        pass

    class Settings(ApiBasedIssueTrackerSettings):
        type: Literal["HTTP"] = "HTTP"

        model_config = SettingsConfigDict(
            env_prefix="HTTP_", env_file=".env", env_file_encoding="utf-8"
        )
