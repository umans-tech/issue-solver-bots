from http import HTTPStatus

import pytest
from requests_mock.mocker import Mocker

from issue_solver import IssueInfo
from issue_solver.issue_trackers import GitlabIssueTracker


@pytest.fixture
def gitlab_base_url() -> str:
    return "https://gitlab.example.com"


@pytest.fixture
def project_id() -> str:
    return "123"


@pytest.fixture
def gitlab_tracker(gitlab_base_url: str, project_id: str) -> GitlabIssueTracker:
    """
    A fixture that provides a GitlabIssueTracker instance
    with dummy credentials and project info.
    """
    return GitlabIssueTracker.of(
        base_url=gitlab_base_url,
        private_token="dummy_token",
        api_version="4",
        project_id=project_id,
    )


def test_describe_issue_success(
    gitlab_tracker: GitlabIssueTracker,
    requests_mock: Mocker,
    gitlab_base_url: str,
    project_id: str,
):
    # Given
    issue_iid = "42"
    issue_title = "Something Is Wrong"
    issue_description = "Hi there! there is an issue"
    gitlab_issue_payload = {
        "id": 147307487,
        "iid": int(issue_iid),
        "project_id": int(project_id),
        "title": issue_title,
        "description": issue_description,
    }

    requests_mock.get(
        f"{gitlab_base_url}/api/v4/projects/{project_id}/issues/{issue_iid}",
        json=gitlab_issue_payload,
        status_code=HTTPStatus.OK,
        headers={"Content-Type": "application/json"},
    )

    # When
    issue_info = gitlab_tracker.describe_issue(issue_iid)

    # Then
    assert issue_info == IssueInfo(
        title=issue_title,
        description=issue_description,
    )


def test_describe_issue_not_found(
    gitlab_tracker: GitlabIssueTracker,
    requests_mock: Mocker,
    gitlab_base_url: str,
    project_id: str,
):
    # Given
    issue_iid = "9999"
    requests_mock.get(
        f"{gitlab_base_url}/api/v4/projects/{project_id}/issues/{issue_iid}",
        status_code=HTTPStatus.NOT_FOUND,
        headers={"Content-Type": "application/json"},
        json={"message": "404 Issue Not Found"},
    )

    # When
    found_issue_info = gitlab_tracker.describe_issue(issue_iid)

    # Then
    assert not found_issue_info


def test_describe_issue_unauthorized(
    gitlab_tracker: GitlabIssueTracker,
    requests_mock: Mocker,
    gitlab_base_url: str,
    project_id: str,
):
    # Given
    issue_iid = "42"
    requests_mock.get(
        f"{gitlab_base_url}/api/v4/projects/{project_id}/issues/{issue_iid}",
        status_code=HTTPStatus.FORBIDDEN,
        json={"message": "401 Unauthorized"},
        headers={"Content-Type": "application/json"},
    )

    # When, Then
    with pytest.raises(PermissionError):
        gitlab_tracker.describe_issue(issue_iid)


def test_describe_issue_forbidden(
    gitlab_tracker: GitlabIssueTracker,
    requests_mock: Mocker,
    gitlab_base_url: str,
    project_id: str,
):
    # Given
    issue_iid = "42"
    requests_mock.get(
        f"{gitlab_base_url}/api/v4/projects/{project_id}/issues/{issue_iid}",
        status_code=HTTPStatus.FORBIDDEN,
        json={"message": "403 Forbidden"},
        headers={"Content-Type": "application/json"},
    )

    # When, Then
    with pytest.raises(PermissionError):
        gitlab_tracker.describe_issue(issue_iid)


def test_describe_issue_missing_description_field(
    gitlab_tracker: GitlabIssueTracker,
    requests_mock: Mocker,
    gitlab_base_url: str,
    project_id: str,
):
    # Given
    issue_iid = "1234"
    # JSON has 'title' but no 'description'
    gitlab_issue_payload = {
        "id": 1111111,
        "iid": int(issue_iid),
        "project_id": int(project_id),
        "title": "No Description Found",
    }
    requests_mock.get(
        f"{gitlab_base_url}/api/v4/projects/{project_id}/issues/{issue_iid}",
        json=gitlab_issue_payload,
        status_code=HTTPStatus.OK,
        headers={"Content-Type": "application/json"},
    )

    # When
    issue_info = gitlab_tracker.describe_issue(issue_iid)

    # Then
    assert issue_info == IssueInfo(title="No Description Found", description="")


def test_describe_issue_server_error(
    gitlab_tracker: GitlabIssueTracker,
    requests_mock: Mocker,
    gitlab_base_url: str,
    project_id: str,
):
    # Given
    issue_iid = "50"
    requests_mock.get(
        f"{gitlab_base_url}/api/v4/projects/{project_id}/issues/{issue_iid}",
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        headers={"Content-Type": "application/json"},
        json={"message": "Server error"},
    )

    # When, Then
    with pytest.raises(RuntimeError):
        gitlab_tracker.describe_issue(issue_iid)
