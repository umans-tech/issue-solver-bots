from http import HTTPStatus
from pathlib import Path
from typing import Self, Literal

import requests
from pydantic import AnyUrl, Field
from pydantic_settings import SettingsConfigDict

from issue_solver.issues.issue import (
    IssueId,
    IssueInternalId,
    IssueReference,
    IssueInfo,
)
from issue_solver.issues.trackers.issue_tracker import IssueTracker
from issue_solver.issues.trackers.settings import ApiBasedIssueTrackerSettings


class TrelloObjectType(str):
    CARD = "CARD"


class TrelloCardInternalId(IssueInternalId):
    type: Literal["CARD"] = "CARD"


class TrelloIssueTracker(IssueTracker):
    def __init__(self, base_url: str, api_key: str, api_token: str) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.api_token = api_token

    @classmethod
    def of(cls, settings: "TrelloIssueTracker.Settings") -> Self:
        return cls(
            base_url=settings.versioned_base_url,
            api_key=settings.api_key,
            api_token=settings.private_token,
        )

    def describe_issue(self, issue_reference: IssueReference) -> IssueInfo | None:
        path = self.get_issue_path(issue_reference)
        params = {
            "key": self.api_key,
            "token": self.api_token,
        }
        try:
            response = requests.get(f"{self.base_url}{path}", params=params)
            if response.status_code == HTTPStatus.NOT_FOUND:
                return None
            if response.status_code in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}:
                raise self.permission_error(response, path, response.status_code)
            if not response.ok:
                raise RuntimeError(
                    f"Failed to get card {path} with status code {response.status_code}",
                    response.text,
                )

            data = response.json()
            title = data.get("name", "")
            desc = data.get("desc", "")
            return IssueInfo(title=title, description=desc)
        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"Failed to get card from {self.base_url}{path}",
                e,
            )

    def permission_error(
        self, response, get_issue_path: str, response_code: int | None = None
    ) -> PermissionError:
        return PermissionError(
            f"Unauthorized call to {self.base_url}{get_issue_path} with status code {response_code}",
            response.text,
        )

    @staticmethod
    def get_issue_path(issue_reference: IssueReference) -> str:
        match issue_reference:
            case TrelloCardInternalId():
                return f"/cards/{issue_reference.iid}"
            case IssueId():
                return f"/cards/{issue_reference.id}"
            case Path():
                return f"/{issue_reference}"
            case _:
                raise ValueError(f"Unsupported reference: {issue_reference}")

    class Settings(ApiBasedIssueTrackerSettings):
        type: Literal["TRELLO"] = "TRELLO"
        base_url: AnyUrl = Field(
            description="Base URL for Trello API",
            default=AnyUrl("https://api.trello.com"),
        )
        api_version: str = Field(
            description="API version for Trello API",
            default="1",
        )
        api_key: str = Field(description="Trello API key (developer key)")
        private_token: str = Field(description="Trello user token (private token)")
        model_config = SettingsConfigDict(
            env_prefix="TRELLO_",
            env_file=".env",
            env_file_encoding="utf-8",
        )
