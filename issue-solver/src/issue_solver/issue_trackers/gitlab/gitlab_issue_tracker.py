from http import HTTPStatus
from typing import Self

import gitlab

from issue_solver.issue_trackers.gitlab.settings import GitlabIssueTrackerSettings
from issue_solver.issue_trackers.issue_tracker import IssueTracker, IssueInfo


class GitlabIssueTracker(IssueTracker):
    def __init__(self, gitlab_client: gitlab.Gitlab, project_id: str | None) -> None:
        self.gitlab_client = gitlab_client
        self.project_id = project_id

    def describe_issue(self, issue_iid: str) -> IssueInfo | None:
        get_issue_path = f"/projects/{self.project_id}/issues/{issue_iid}"
        try:
            issue_response = self.gitlab_client.http_get(get_issue_path)
            return IssueInfo(
                title=issue_response.get("title", ""),
                description=issue_response.get("description", ""),
            )
        except gitlab.exceptions.GitlabHttpError as e:
            if e.response_code == HTTPStatus.NOT_FOUND:
                return None
            if e.response_code in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}:
                raise PermissionError(
                    f"Unauthorized call to {self.gitlab_client.api_url}/{get_issue_path} with status code {e.response_code}",
                    e,
                )
            raise RuntimeError(
                f"Failed to get issue {issue_iid} from {self.gitlab_client.api_url}/{get_issue_path} with status code {e.response_code}",
                e,
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
        return cls(gitlab_client, settings.project_id)
