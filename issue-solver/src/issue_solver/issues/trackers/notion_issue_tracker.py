from http import HTTPStatus
from pathlib import Path
from typing import Self, Literal, Any

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


class NotionObjectType(str):
    PAGE = "PAGE"


class NotionPageInternalId(IssueInternalId):
    type: Literal["PAGE"] = "PAGE"


class NotionIssueTracker(IssueTracker):
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token

    @classmethod
    def of(cls, settings: "NotionIssueTracker.Settings") -> Self:
        return cls(
            base_url=str(settings.base_url),
            token=settings.private_token,
        )

    def describe_issue(self, issue_reference: IssueReference) -> IssueInfo | None:
        path = self.get_issue_path(issue_reference)
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
        }
        try:
            response = requests.get(f"{self.base_url}{path}", headers=headers)
            if response.status_code == HTTPStatus.NOT_FOUND:
                return None
            if response.status_code in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}:
                raise self.permission_error(response, path, response.status_code)
            if not response.ok:
                raise RuntimeError(
                    f"Failed to get Notion page {path} with status code {response.status_code}",
                    response.text,
                )

            data = response.json()

            properties = data.get("properties", {})
            title_property = properties.get("title", {})
            page_title = parse_title(title_property)

            desc_property = properties.get("Description", {})
            page_desc = parse_description(desc_property)

            return IssueInfo(title=page_title, description=page_desc)
        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"Failed to get Notion page from {self.base_url}{path}",
                e,
            )

    def permission_error(
        self, response, path: str, response_code: int | None = None
    ) -> PermissionError:
        return PermissionError(
            f"Unauthorized call to {self.base_url}{path} with status code {response_code}",
            response.text,
        )

    @staticmethod
    def get_issue_path(issue_reference: IssueReference) -> str:
        match issue_reference:
            case NotionPageInternalId():
                return f"/pages/{issue_reference.iid}"
            case IssueId():
                return f"/pages/{issue_reference.id}"
            case Path():
                return f"/{issue_reference}"
            case _:
                raise ValueError(f"Unsupported reference: {issue_reference}")

    class Settings(ApiBasedIssueTrackerSettings):
        type: Literal["NOTION"] = "NOTION"
        base_url: AnyUrl = Field(
            description="Base URL for Notion API",
            default=AnyUrl("https://api.notion.com/v1"),
        )
        private_token: str = Field(description="Bearer token for Notion")

        model_config = SettingsConfigDict(
            env_prefix="NOTION_",
            env_file=".env",
            env_file_encoding="utf-8",
        )


def parse_title(title_property: dict[str, Any]) -> str:
    page_title = ""
    if isinstance(title_property.get("title"), list):
        page_title = " ".join(
            t["plain_text"] for t in title_property["title"] if "plain_text" in t
        )
    return page_title


def parse_description(desc_property: dict[str, Any]) -> str:
    page_desc = ""
    if isinstance(desc_property.get("rich_text"), list):
        page_desc = " ".join(
            t["plain_text"] for t in desc_property["rich_text"] if "plain_text" in t
        )
    return page_desc
