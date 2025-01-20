from http import HTTPStatus
from pathlib import Path

import pytest
from pydantic_core import Url
from requests_mock import Mocker

from issue_solver.issues.issue import IssueId, IssueInternalId, IssueInfo
from issue_solver.issues.trackers.github_issue_tracker import (
    GithubIssueTracker,
    PullRequestInternalId,
)


@pytest.fixture
def github_base_url() -> str:
    return "https://api.github.com"


@pytest.fixture
def github_tracker(github_base_url: str) -> GithubIssueTracker:
    return GithubIssueTracker.of(
        settings=GithubIssueTracker.Settings(
            base_url=Url(github_base_url),
            private_token="dummy_github_token",
            api_version="v3",
        )
    )


def test_describe_issue_by_iid_success(
    github_tracker: GithubIssueTracker, requests_mock: Mocker
):
    # Given
    owner_repo = "octocat/Hello-World"
    iid = "42"
    issue_ref = IssueInternalId(project_id=owner_repo, iid=iid)
    issue_title = "Fix bug"
    issue_body = "Detailed description"

    requests_mock.get(
        f"https://api.github.com/repos/{owner_repo}/issues/{iid}",
        json={"title": issue_title, "body": issue_body},
        status_code=HTTPStatus.OK,
    )

    # When
    issue_info = github_tracker.describe_issue(issue_ref)

    # Then
    assert issue_info == IssueInfo(title=issue_title, description=issue_body)


def test_describe_issue_not_found(
    github_tracker: GithubIssueTracker, requests_mock: Mocker
):
    owner_repo = "octocat/Hello-World"
    iid = "9999"
    issue_ref = IssueInternalId(project_id=owner_repo, iid=iid)

    requests_mock.get(
        f"https://api.github.com/repos/{owner_repo}/issues/{iid}",
        status_code=HTTPStatus.NOT_FOUND,
    )
    # No JSON body needed here, 404 is enough

    assert github_tracker.describe_issue(issue_ref) is None


def test_describe_issue_unauthorized(
    github_tracker: GithubIssueTracker, requests_mock: Mocker
):
    owner_repo = "octocat/Hello-World"
    iid = "123"
    issue_ref = IssueInternalId(project_id=owner_repo, iid=iid)

    requests_mock.get(
        f"https://api.github.com/repos/{owner_repo}/issues/{iid}",
        status_code=HTTPStatus.UNAUTHORIZED,
        json={"message": "Bad credentials"},
    )

    with pytest.raises(PermissionError):
        github_tracker.describe_issue(issue_ref)


def test_describe_issue_forbidden(
    github_tracker: GithubIssueTracker, requests_mock: Mocker
):
    owner_repo = "octocat/Hello-World"
    iid = "124"
    issue_ref = IssueInternalId(project_id=owner_repo, iid=iid)

    requests_mock.get(
        f"https://api.github.com/repos/{owner_repo}/issues/{iid}",
        status_code=HTTPStatus.FORBIDDEN,
        json={"message": "Access forbidden"},
    )

    with pytest.raises(PermissionError):
        github_tracker.describe_issue(issue_ref)


def test_describe_issue_server_error(
    github_tracker: GithubIssueTracker, requests_mock: Mocker
):
    owner_repo = "octocat/Hello-World"
    iid = "500"
    issue_ref = IssueInternalId(project_id=owner_repo, iid=iid)

    requests_mock.get(
        f"https://api.github.com/repos/{owner_repo}/issues/{iid}",
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        json={"message": "Server error"},
    )

    with pytest.raises(RuntimeError):
        github_tracker.describe_issue(issue_ref)


def test_describe_pr_success(github_tracker: GithubIssueTracker, requests_mock: Mocker):
    owner_repo = "octocat/Hello-World"
    pr_iid = "777"
    issue_ref = PullRequestInternalId(project_id=owner_repo, iid=pr_iid)
    title = "Add a new feature"
    body = "Here is the body for the PR"

    requests_mock.get(
        f"https://api.github.com/repos/{owner_repo}/pulls/{pr_iid}",
        status_code=HTTPStatus.OK,
        json={"title": title, "body": body},
    )

    info = github_tracker.describe_issue(issue_ref)
    assert info == IssueInfo(title=title, description=body)


def test_describe_global_issue_id_not_supported(github_tracker: GithubIssueTracker):
    # GitHub n'a pas d'ID global, on s'attend à une erreur
    issue_ref = IssueId("42")
    with pytest.raises(RuntimeError) as exc:
        github_tracker.describe_issue(issue_ref)
    assert "does not support global issue IDs" in str(exc.value)


def test_describe_issue_by_path_success(
    github_tracker: GithubIssueTracker, requests_mock: Mocker
):
    path_ref = Path("octocat/Hello-World/issues/77")
    title = "Issue from path"
    body = "some body"

    requests_mock.get(
        "https://api.github.com/repos/octocat/Hello-World/issues/77",
        status_code=HTTPStatus.OK,
        json={"title": title, "body": body},
    )

    info = github_tracker.describe_issue(path_ref)
    assert info == IssueInfo(title=title, description=body)
