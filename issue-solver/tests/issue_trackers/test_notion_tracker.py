from http import HTTPStatus
from pathlib import Path

import pytest
from pydantic_core import Url
from requests_mock import Mocker

from issue_solver.issues.issue import IssueId, IssueInfo
from issue_solver.issues.trackers.notion_issue_tracker import (
    NotionIssueTracker,
    NotionPageInternalId,
)


@pytest.fixture
def notion_base_url() -> str:
    return "https://api.notion.com/v1"


@pytest.fixture
def notion_tracker(notion_base_url: str) -> NotionIssueTracker:
    return NotionIssueTracker.of(
        settings=NotionIssueTracker.Settings(
            base_url=Url(notion_base_url),
            private_token="dummy_notion_token",
        )
    )


def test_describe_page_success(
    notion_tracker: NotionIssueTracker, requests_mock: Mocker, notion_base_url: str
):
    page_id = "abc123"
    issue_ref = NotionPageInternalId(project_id="someWorkspace", iid=page_id)

    mock_response = {
        "object": "page",
        "id": page_id,
        "properties": {
            "title": {"title": [{"plain_text": "My Notion Page Title"}]},
            "Description": {"rich_text": [{"plain_text": "A little description"}]},
        },
    }

    requests_mock.get(
        f"{notion_base_url}/pages/{page_id}",
        status_code=HTTPStatus.OK,
        json=mock_response,
    )

    info = notion_tracker.describe_issue(issue_ref)
    assert info == IssueInfo(
        title="My Notion Page Title",
        description="A little description",
    )


def test_describe_page_not_found(
    notion_tracker: NotionIssueTracker, requests_mock: Mocker, notion_base_url: str
):
    page_id = "xyz999"
    issue_ref = NotionPageInternalId(project_id="someWorkspace", iid=page_id)

    requests_mock.get(
        f"{notion_base_url}/pages/{page_id}",
        status_code=HTTPStatus.NOT_FOUND,
        json={"object": "error", "status": 404, "message": "Page not found"},
    )

    assert notion_tracker.describe_issue(issue_ref) is None


def test_describe_page_unauthorized(
    notion_tracker: NotionIssueTracker, requests_mock: Mocker, notion_base_url: str
):
    page_id = "secretPage"
    issue_ref = NotionPageInternalId(project_id="someWorkspace", iid=page_id)

    requests_mock.get(
        f"{notion_base_url}/pages/{page_id}",
        status_code=HTTPStatus.UNAUTHORIZED,
        json={"object": "error", "status": 401, "message": "Unauthorized"},
    )

    with pytest.raises(PermissionError):
        notion_tracker.describe_issue(issue_ref)


def test_describe_page_forbidden(
    notion_tracker: NotionIssueTracker, requests_mock: Mocker, notion_base_url: str
):
    page_id = "forbiddenPage"
    issue_ref = NotionPageInternalId(project_id="someWorkspace", iid=page_id)

    requests_mock.get(
        f"{notion_base_url}/pages/{page_id}",
        status_code=HTTPStatus.FORBIDDEN,
        json={"object": "error", "status": 403, "message": "Forbidden"},
    )

    with pytest.raises(PermissionError):
        notion_tracker.describe_issue(issue_ref)


def test_describe_page_server_error(
    notion_tracker: NotionIssueTracker, requests_mock: Mocker, notion_base_url: str
):
    page_id = "serverError"
    issue_ref = NotionPageInternalId(project_id="someWorkspace", iid=page_id)

    requests_mock.get(
        f"{notion_base_url}/pages/{page_id}",
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        json={"object": "error", "status": 500, "message": "Internal Server Error"},
    )

    with pytest.raises(RuntimeError):
        notion_tracker.describe_issue(issue_ref)


def test_describe_page_by_issue_id(
    notion_tracker: NotionIssueTracker, requests_mock: Mocker, notion_base_url: str
):
    page_id = "AAAA1111"
    issue_ref = IssueId(page_id)

    mock_response = {
        "object": "page",
        "id": page_id,
        "properties": {
            "title": {
                "title": [{"plain_text": "Global ID Title"}],
            },
            "Description": {
                "rich_text": [{"plain_text": "Global ID Desc"}],
            },
        },
    }

    requests_mock.get(
        f"{notion_base_url}/pages/{page_id}",
        status_code=HTTPStatus.OK,
        json=mock_response,
    )

    info = notion_tracker.describe_issue(issue_ref)
    assert info == IssueInfo(title="Global ID Title", description="Global ID Desc")


def test_describe_page_by_path(
    notion_tracker: NotionIssueTracker, requests_mock: Mocker, notion_base_url: str
):
    path_ref = Path("pages/ZZZZ2222")

    mock_response = {
        "object": "page",
        "id": "ZZZZ2222",
        "properties": {
            "title": {"title": [{"plain_text": "Path Title"}]},
            "Description": {"rich_text": [{"plain_text": "Path Desc"}]},
        },
    }

    requests_mock.get(
        f"{notion_base_url}/pages/ZZZZ2222",
        status_code=HTTPStatus.OK,
        json=mock_response,
    )

    info = notion_tracker.describe_issue(path_ref)
    assert info == IssueInfo(title="Path Title", description="Path Desc")
