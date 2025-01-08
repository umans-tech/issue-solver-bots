from typing import Literal

from pydantic_settings import SettingsConfigDict

from issue_solver.issue_trackers.settings import ApiBasedIssueTrackerSettings


class HttpBasedIssueTrackerSettings(ApiBasedIssueTrackerSettings):
    type: Literal["HTTP"] = "HTTP"

    model_config = SettingsConfigDict(
        env_prefix="HTTP_", env_file=".env", env_file_encoding="utf-8"
    )
