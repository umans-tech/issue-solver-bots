from enum import StrEnum
from http import HTTPStatus
from pathlib import Path
from typing import Literal, Self

import requests
from pydantic import AnyUrl, Field
from pydantic_settings import SettingsConfigDict

from issue_solver.issues.issue import (
    IssueReference,
    IssueInfo,
    IssueInternalId,
    IssueId,
)
from issue_solver.issues.trackers.issue_tracker import (
    IssueTracker,
)
from issue_solver.issues.trackers.settings import ApiBasedIssueTrackerSettings


class GithubObjectType(StrEnum):
    ISSUE = "ISSUE"
    MR = "MR"


class PullRequestInternalId(IssueInternalId):
    type: Literal["PR"] = "PR"


class GithubIssueTracker(IssueTracker):
    def __init__(self, settings: "GithubIssueTracker.Settings") -> None:
        self.settings = settings

    @classmethod
    def of(cls, settings: "GithubIssueTracker.Settings") -> Self:
        return cls(settings=settings)

    def describe_issue(self, issue_reference: IssueReference) -> IssueInfo | None:
        issue_path = self.get_issue_path(issue_reference)
        headers = {
            "Accept": f"application/vnd.github.{self.settings.api_version}+json",
            "Authorization": f"Bearer {self.settings.private_token}"
            if self.settings.private_token
            else None,
        }
        try:
            response = requests.get(
                f"{self.settings.base_url}{issue_path}", headers=headers
            )
            if response.status_code == HTTPStatus.NOT_FOUND:
                return None
            if response.status_code in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}:
                raise self.permission_error(response, issue_path, response.status_code)
            if not response.ok:
                raise RuntimeError(
                    f"Failed to get issue from {self.settings.base_url}{issue_path} with status code {response.status_code}",
                    response.text,
                )

            data = response.json()
            title = data.get("title", "")
            body = data.get("body", "")
            return IssueInfo(title=title, description=body)
        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"Failed to get issue from {self.settings.base_url}{issue_path}",
                e,
            )

    def permission_error(
        self, response, get_issue_path: str, response_code: int | None = None
    ) -> PermissionError:
        return PermissionError(
            f"Unauthorized call to {self.settings.base_url}{get_issue_path} with status code {response_code}",
            response.text,
        )

    @staticmethod
    def get_issue_path(issue_reference: IssueReference) -> str:
        match issue_reference:
            case PullRequestInternalId():
                owner_repo = issue_reference.project_id
                return f"repos/{owner_repo}/pulls/{issue_reference.iid}"
            case IssueInternalId():
                owner_repo = issue_reference.project_id
                return f"repos/{owner_repo}/issues/{issue_reference.iid}"
            case IssueId():
                raise RuntimeError("GitHub does not support global issue IDs")
            case Path():
                return f"repos/{issue_reference}"
            case _:
                raise ValueError(f"Unsupported reference: {issue_reference}")

    class Settings(ApiBasedIssueTrackerSettings):
        type: Literal["GITHUB"] = "GITHUB"
        base_url: AnyUrl = Field(
            description="Base URL for the GitHub.",
            default=AnyUrl("https://api.github.com"),
        )
        object_type: GithubObjectType = Field(
            default=GithubObjectType.ISSUE,
            description="Determines whether we retrieve from an ISSUE or a MR in GitLab.",
        )

        model_config = SettingsConfigDict(
            env_prefix="GITHUB_", env_file=".env", env_file_encoding="utf-8"
        )
