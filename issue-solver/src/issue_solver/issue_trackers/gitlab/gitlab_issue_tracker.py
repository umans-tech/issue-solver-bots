from http import HTTPStatus
from pathlib import Path
from typing import Self, assert_never

import gitlab

from issue_solver.issue_trackers.gitlab.settings import GitlabIssueTrackerSettings
from issue_solver.issue_trackers.issue_tracker import (
    IssueTracker,
    IssueInfo,
    IssueReference,
    IssueInternalId,
    IssueId,
)


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
        settings: GitlabIssueTrackerSettings,
    ) -> Self:
        gitlab_client = gitlab.Gitlab(
            url=str(settings.base_url),
            private_token=settings.private_token,
            api_version=settings.api_version,
        )
        return cls(gitlab_client)
