from enum import StrEnum
from http import HTTPStatus
from pathlib import Path
from typing import Self, assert_never, Literal

import gitlab
from pydantic import AnyUrl, Field
from pydantic_settings import SettingsConfigDict

from issue_solver.issues.issue import (
    IssueId,
    IssueInternalId,
    IssueReference,
    IssueInfo,
)
from issue_solver.issues.trackers.issue_tracker import (
    IssueTracker,
)
from issue_solver.issues.trackers.settings import ApiBasedIssueTrackerSettings


class GitlabObjectType(StrEnum):
    ISSUE = "ISSUE"
    MR = "MR"


class MergeRequestInternalId(IssueInternalId):
    type: Literal["MR"] = "MR"


class GitlabIssueTracker(IssueTracker):
    def __init__(self, gitlab_client: gitlab.Gitlab) -> None:
        self.gitlab_client = gitlab_client

    def describe_issue(self, issue_reference: IssueReference) -> IssueInfo | None:
        issue_path = self.get_issue_path(issue_reference)
        try:
            issue_response = self.gitlab_client.http_get(issue_path)
            return IssueInfo(
                title=issue_response.get("title", ""),
                description=issue_response.get("description", ""),
            )
        except gitlab.exceptions.GitlabHttpError as e:
            if e.response_code == HTTPStatus.NOT_FOUND:
                return None
            if e.response_code in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}:
                raise self.permission_error(e, issue_path, e.response_code)
            raise RuntimeError(
                f"Failed to get issue {issue_reference} from {self.gitlab_client.api_url}/{issue_path} with status code {e.response_code}",
                e,
            )
        except gitlab.exceptions.GitlabAuthenticationError as e:
            raise self.permission_error(e, issue_path, e.response_code)
        except Exception as e:
            raise RuntimeError(
                f"Failed to get issue {issue_reference} from {self.gitlab_client.api_url}/{issue_path}",
                e,
            )

    @staticmethod
    def get_issue_path(issue_reference: IssueReference) -> str:
        match issue_reference:
            case MergeRequestInternalId():
                issue_path = f"/projects/{issue_reference.project_id}/merge_requests/{issue_reference.iid}"
            case IssueInternalId():
                issue_path = f"/projects/{issue_reference.project_id}/issues/{issue_reference.iid}"
            case IssueId():
                issue_path = f"/issues/{issue_reference.id}"
            case Path():
                issue_path = f"/{issue_reference}"
            case _:
                assert_never(issue_reference)
        return issue_path

    def permission_error(
        self,
        root_exception: Exception,
        get_issue_path: str,
        response_code: int | None = None,
    ) -> PermissionError:
        return PermissionError(
            f"Unauthorized call to {self.gitlab_client.api_url}/{get_issue_path} with status code {response_code}",
            root_exception,
        )

    @classmethod
    def of(
        cls,
        settings: "GitlabIssueTracker.Settings",
    ) -> Self:
        gitlab_client = gitlab.Gitlab(
            url=str(settings.base_url),
            private_token=settings.private_token,
            api_version=settings.api_version,
        )
        return cls(gitlab_client)

    class Settings(ApiBasedIssueTrackerSettings):
        type: Literal["GITLAB"] = "GITLAB"
        base_url: AnyUrl = Field(
            description="Base URL for the GitLab.",
            default=AnyUrl("https://gitlab.com"),
        )
        api_version: str = Field(
            description="API version for the issue tracker.", default="4"
        )
        object_type: GitlabObjectType = Field(
            default=GitlabObjectType.ISSUE,
            description="Determines whether we retrieve from an ISSUE or a MR in GitLab.",
        )
        model_config = SettingsConfigDict(
            env_prefix="GITLAB_", env_file=".env", env_file_encoding="utf-8"
        )
