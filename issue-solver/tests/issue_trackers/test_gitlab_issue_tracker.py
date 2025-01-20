from http import HTTPStatus
from pathlib import Path

import pytest
from pydantic import AnyUrl
from requests_mock.mocker import Mocker

from issue_solver.issues.issue import IssueId, IssueInternalId, IssueInfo
from issue_solver.issues.trackers.gitlab_issue_tracker import (
    GitlabIssueTracker,
    MergeRequestInternalId,
)


@pytest.fixture
def gitlab_base_url() -> str:
    return "https://gitlab.example.com"


@pytest.fixture
def gitlab_tracker(gitlab_base_url: str) -> GitlabIssueTracker:
    """
    A fixture that provides a GitlabIssueTracker instance
    with dummy credentials and project info.
    """
    return GitlabIssueTracker.of(
        settings=GitlabIssueTracker.Settings(
            base_url=AnyUrl(gitlab_base_url),
            private_token="dummy_token",
            api_version="4",
        )
    )


def test_describe_issue_by_iid_success(
    gitlab_tracker: GitlabIssueTracker,
    requests_mock: Mocker,
    gitlab_base_url: str,
):
    # Given
    issue_iid = "42"
    project_id = "1234"
    issue_ref = IssueInternalId(project_id=project_id, iid=issue_iid)
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
    issue_info = gitlab_tracker.describe_issue(issue_ref)

    # Then
    assert issue_info == IssueInfo(
        title=issue_title,
        description=issue_description,
    )


def test_describe_issue_by_iid_not_found(
    gitlab_tracker: GitlabIssueTracker,
    requests_mock: Mocker,
    gitlab_base_url: str,
):
    # Given
    issue_iid = "9999"
    project_id = "1234"
    issue_ref = IssueInternalId(project_id=project_id, iid=issue_iid)
    requests_mock.get(
        f"{gitlab_base_url}/api/v4/projects/{project_id}/issues/{issue_iid}",
        status_code=HTTPStatus.NOT_FOUND,
        headers={"Content-Type": "application/json"},
        json={"message": "404 Issue Not Found"},
    )

    # When
    found_issue_info = gitlab_tracker.describe_issue(issue_ref)

    # Then
    assert not found_issue_info


def test_describe_issue_by_iid_unauthorized(
    gitlab_tracker: GitlabIssueTracker,
    requests_mock: Mocker,
    gitlab_base_url: str,
):
    # Given
    issue_iid = "42"
    project_id = "1000"
    issue_ref = IssueInternalId(project_id=project_id, iid=issue_iid)
    requests_mock.get(
        f"{gitlab_base_url}/api/v4/projects/{project_id}/issues/{issue_iid}",
        status_code=HTTPStatus.UNAUTHORIZED,
        json={"message": "401 Unauthorized"},
        headers={"Content-Type": "application/json"},
    )

    # When, Then
    with pytest.raises(PermissionError):
        gitlab_tracker.describe_issue(issue_ref)


def test_describe_issue_by_iid_forbidden(
    gitlab_tracker: GitlabIssueTracker,
    requests_mock: Mocker,
    gitlab_base_url: str,
):
    # Given
    issue_iid = "42"
    project_id = "1010"
    issue_ref = IssueInternalId(project_id=project_id, iid=issue_iid)
    requests_mock.get(
        f"{gitlab_base_url}/api/v4/projects/{project_id}/issues/{issue_iid}",
        status_code=HTTPStatus.FORBIDDEN,
        json={"message": "403 Forbidden"},
        headers={"Content-Type": "application/json"},
    )

    # When, Then
    with pytest.raises(PermissionError):
        gitlab_tracker.describe_issue(issue_ref)


def test_describe_issue_by_iid_missing_description_field(
    gitlab_tracker: GitlabIssueTracker,
    requests_mock: Mocker,
    gitlab_base_url: str,
):
    # Given
    issue_iid = "1234"
    project_id = "5678"
    issue_ref = IssueInternalId(project_id=project_id, iid=issue_iid)
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
    issue_info = gitlab_tracker.describe_issue(issue_ref)

    # Then
    assert issue_info == IssueInfo(title="No Description Found", description="")


def test_describe_issue_by_iid_server_error(
    gitlab_tracker: GitlabIssueTracker,
    requests_mock: Mocker,
    gitlab_base_url: str,
):
    # Given
    issue_iid = "50"
    project_id = "1234"
    issue_ref = IssueInternalId(project_id=project_id, iid=issue_iid)
    requests_mock.get(
        f"{gitlab_base_url}/api/v4/projects/{project_id}/issues/{issue_iid}",
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        headers={"Content-Type": "application/json"},
        json={"message": "Server error"},
    )

    # When, Then
    with pytest.raises(RuntimeError):
        gitlab_tracker.describe_issue(issue_ref)


def test_describe_issue_by_id_success(
    gitlab_tracker: GitlabIssueTracker, requests_mock: Mocker, gitlab_base_url: str
):
    # Given
    issue_ref = IssueId("42")
    url = f"{gitlab_base_url}/api/v4/issues/42"
    payload = {
        "id": 42,
        "iid": 123,
        "title": "Some Issue",
        "description": "Details here",
    }
    requests_mock.get(
        url,
        json=payload,
        status_code=HTTPStatus.OK,
        headers={"Content-Type": "application/json"},
    )

    # When
    info = gitlab_tracker.describe_issue(issue_ref)

    # Then
    assert info == IssueInfo(title="Some Issue", description="Details here")


def test_describe_issue_by_path_success(
    gitlab_tracker: GitlabIssueTracker, requests_mock: Mocker, gitlab_base_url: str
):
    # Given
    issue_ref = Path("mygroup/myrepo/issues/42")
    payload = {
        "id": 999,
        "iid": 42,
        "title": "Path Issue",
        "description": "Path-based details",
    }
    requests_mock.get(
        f"{gitlab_base_url}/api/v4/mygroup/myrepo/issues/42",
        json=payload,
        status_code=HTTPStatus.OK,
        headers={"Content-Type": "application/json"},
    )

    # When
    info = gitlab_tracker.describe_issue(issue_ref)

    # Then
    assert info == IssueInfo(title="Path Issue", description="Path-based details")


def test_describe_issue_by_id_not_found(
    gitlab_tracker: GitlabIssueTracker, requests_mock: Mocker, gitlab_base_url: str
):
    # Given
    issue_ref = IssueId("9999")
    url = f"{gitlab_base_url}/api/v4/issues/9999"

    # When
    requests_mock.get(
        url,
        status_code=HTTPStatus.NOT_FOUND,
        json={"message": "Not Found"},
        headers={"Content-Type": "application/json"},
    )

    # Then
    assert gitlab_tracker.describe_issue(issue_ref) is None


def test_describe_issue_by_path_not_found(
    gitlab_tracker: GitlabIssueTracker, requests_mock: Mocker, gitlab_base_url: str
):
    # Given
    issue_ref = Path("mygroup/myrepo/issues/9999")
    url = f"{gitlab_base_url}/api/v4/mygroup/myrepo/issues/9999"

    # When
    requests_mock.get(
        url,
        status_code=HTTPStatus.NOT_FOUND,
        json={"message": "Not Found"},
        headers={"Content-Type": "application/json"},
    )

    # Then
    assert gitlab_tracker.describe_issue(issue_ref) is None


def test_describe_issue_by_id_unauthorized(
    gitlab_tracker: GitlabIssueTracker, requests_mock: Mocker, gitlab_base_url: str
):
    # Given
    issue_ref = IssueId("42")
    requests_mock.get(
        f"{gitlab_base_url}/api/v4/issues/42", status_code=HTTPStatus.UNAUTHORIZED
    )

    # When, Then
    with pytest.raises(PermissionError):
        gitlab_tracker.describe_issue(issue_ref)


def test_describe_issue_by_path_missing_description(
    gitlab_tracker: GitlabIssueTracker, requests_mock: Mocker, gitlab_base_url: str
):
    # Given
    issue_ref = Path("group/repo/issues/1234")
    payload = {"id": 1111, "iid": 1234, "title": "No description here"}
    requests_mock.get(
        f"{gitlab_base_url}/api/v4/group/repo/issues/1234",
        json=payload,
        status_code=HTTPStatus.OK,
        headers={"Content-Type": "application/json"},
    )

    # When
    info = gitlab_tracker.describe_issue(issue_ref)

    # Then
    assert info == IssueInfo(title="No description here", description="")


def test_describe_issue_by_path_unauthorized(
    gitlab_tracker: GitlabIssueTracker, requests_mock: Mocker, gitlab_base_url: str
):
    # Given
    issue_ref = Path("group/repo/issues/1234987")
    requests_mock.get(
        f"{gitlab_base_url}/api/v4/group/repo/issues/1234987",
        status_code=HTTPStatus.UNAUTHORIZED,
    )

    # When, Then
    with pytest.raises(PermissionError):
        gitlab_tracker.describe_issue(issue_ref)


def test_describe_issue_by_id_server_error(
    gitlab_tracker: GitlabIssueTracker, requests_mock: Mocker, gitlab_base_url: str
):
    # Given
    issue_ref = IssueId("50")
    requests_mock.get(
        f"{gitlab_base_url}/api/v4/issues/50",
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        json={"message": "Error"},
        headers={"Content-Type": "application/json"},
    )

    # When, Then
    with pytest.raises(RuntimeError):
        gitlab_tracker.describe_issue(issue_ref)


def test_describe_issue_by_mrid_success(
    gitlab_tracker: GitlabIssueTracker,
    requests_mock: Mocker,
    gitlab_base_url: str,
):
    # Given
    mr_iid = "42"
    project_id = "1234"
    issue_ref = MergeRequestInternalId(project_id=project_id, iid=mr_iid)
    issue_title = "Something Is Wrong"
    issue_description = "Hi there! there is an issue"
    gitlab_mr_payload = {
        "id": 147307487,
        "iid": int(mr_iid),
        "project_id": int(project_id),
        "title": issue_title,
        "description": issue_description,
    }

    requests_mock.get(
        f"{gitlab_base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}",
        json=gitlab_mr_payload,
        status_code=HTTPStatus.OK,
        headers={"Content-Type": "application/json"},
    )

    # When
    issue_info = gitlab_tracker.describe_issue(issue_ref)

    # Then
    assert issue_info == IssueInfo(
        title=issue_title,
        description=issue_description,
    )
