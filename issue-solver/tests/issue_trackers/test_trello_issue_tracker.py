from http import HTTPStatus
from pathlib import Path

import pytest
from pydantic_core import Url
from requests_mock import Mocker

from issue_solver.issues.issue import IssueId, IssueInfo
from issue_solver.issues.trackers.trello_issue_tracker import (
    TrelloIssueTracker,
    TrelloCardInternalId,
)


@pytest.fixture
def trello_base_url() -> str:
    return "https://api.trello.com"


@pytest.fixture
def trello_api_version() -> str:
    return "1"


@pytest.fixture
def trello_versioned_base_url() -> str:
    return "https://api.trello.com/1"


@pytest.fixture
def trello_tracker(trello_base_url: str, trello_api_version: str) -> TrelloIssueTracker:
    return TrelloIssueTracker.of(
        settings=TrelloIssueTracker.Settings(
            base_url=Url(trello_base_url),
            api_version=trello_api_version,
            api_key="dummy_key",
            private_token="dummy_token",
        )
    )


def test_describe_card_success(
    trello_tracker: TrelloIssueTracker,
    requests_mock: Mocker,
    trello_versioned_base_url: str,
):
    card_id = "abcd1234"
    issue_ref = TrelloCardInternalId(project_id="someBoard", iid=card_id)
    card_name = "Fix login bug"
    card_desc = "Users cannot log in..."

    requests_mock.get(
        f"{trello_versioned_base_url}/cards/{card_id}?key=dummy_key&token=dummy_token",
        status_code=HTTPStatus.OK,
        json={"name": card_name, "desc": card_desc},
    )

    info = trello_tracker.describe_issue(issue_ref)
    assert info == IssueInfo(title=card_name, description=card_desc)


def test_describe_card_not_found(
    trello_tracker: TrelloIssueTracker,
    requests_mock: Mocker,
    trello_versioned_base_url: str,
):
    card_id = "fake9999"
    issue_ref = TrelloCardInternalId(project_id="someBoard", iid=card_id)

    requests_mock.get(
        f"{trello_versioned_base_url}/cards/{card_id}?key=dummy_key&token=dummy_token",
        status_code=HTTPStatus.NOT_FOUND,
        json={"message": "Card not found"},
    )

    assert trello_tracker.describe_issue(issue_ref) is None


def test_describe_card_unauthorized(
    trello_tracker: TrelloIssueTracker,
    requests_mock: Mocker,
    trello_versioned_base_url: str,
):
    card_id = "authFail"
    issue_ref = TrelloCardInternalId(project_id="someBoard", iid=card_id)

    requests_mock.get(
        f"{trello_versioned_base_url}/cards/{card_id}?key=dummy_key&token=dummy_token",
        status_code=HTTPStatus.UNAUTHORIZED,
        json={"message": "Invalid token"},
    )

    with pytest.raises(PermissionError):
        trello_tracker.describe_issue(issue_ref)


def test_describe_card_forbidden(
    trello_tracker: TrelloIssueTracker,
    requests_mock: Mocker,
    trello_versioned_base_url: str,
):
    card_id = "forbiddenCard"
    issue_ref = TrelloCardInternalId(project_id="someBoard", iid=card_id)

    requests_mock.get(
        f"{trello_versioned_base_url}/cards/{card_id}?key=dummy_key&token=dummy_token",
        status_code=HTTPStatus.FORBIDDEN,
        json={"message": "Access to that card is forbidden"},
    )

    with pytest.raises(PermissionError):
        trello_tracker.describe_issue(issue_ref)


def test_describe_card_server_error(
    trello_tracker: TrelloIssueTracker,
    requests_mock: Mocker,
    trello_versioned_base_url: str,
):
    card_id = "serverError"
    issue_ref = TrelloCardInternalId(project_id="someBoard", iid=card_id)

    requests_mock.get(
        f"{trello_versioned_base_url}/cards/{card_id}?key=dummy_key&token=dummy_token",
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        json={"message": "Server meltdown"},
    )

    with pytest.raises(RuntimeError):
        trello_tracker.describe_issue(issue_ref)


def test_describe_card_by_id_success(
    trello_tracker: TrelloIssueTracker,
    requests_mock: Mocker,
    trello_versioned_base_url: str,
):
    card_id = "ZZZZ9999"
    issue_ref = IssueId(card_id)
    name = "Card from global ID"
    desc = "Some detail"

    requests_mock.get(
        f"{trello_versioned_base_url}/cards/{card_id}?key=dummy_key&token=dummy_token",
        status_code=HTTPStatus.OK,
        json={"name": name, "desc": desc},
    )

    info = trello_tracker.describe_issue(issue_ref)
    assert info == IssueInfo(title=name, description=desc)


def test_describe_card_by_path(
    trello_tracker: TrelloIssueTracker,
    requests_mock: Mocker,
    trello_versioned_base_url: str,
):
    path_ref = Path("cards/TTTT1234")
    card_name = "Card from path"
    card_desc = "Desc from path"

    requests_mock.get(
        f"{trello_versioned_base_url}/cards/TTTT1234?key=dummy_key&token=dummy_token",
        status_code=HTTPStatus.OK,
        json={"name": card_name, "desc": card_desc},
    )

    info = trello_tracker.describe_issue(path_ref)
    assert info == IssueInfo(title=card_name, description=card_desc)
