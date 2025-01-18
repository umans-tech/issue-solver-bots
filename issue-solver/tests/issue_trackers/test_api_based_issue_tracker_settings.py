from pydantic_core import Url

from issue_solver.issues.trackers.settings import ApiBasedIssueTrackerSettings


class ConcreteApiBasedIssueTrackerSettings(ApiBasedIssueTrackerSettings):
    pass


def test_versioned_base_url_with_api_version() -> None:
    # Given
    base_url = Url("https://api.tracker.com")

    # When
    settings = ConcreteApiBasedIssueTrackerSettings(
        base_url=base_url, private_token="dummy_token", api_version="1"
    )

    # Then
    assert settings.versioned_base_url == "https://api.tracker.com/1"


def test_versioned_base_url_without_api_version() -> None:
    # Given
    base_url = Url("https://api.tracker.com")

    # When
    settings = ConcreteApiBasedIssueTrackerSettings(
        base_url=base_url, private_token="dummy_token"
    )

    # Then
    assert settings.versioned_base_url == "https://api.tracker.com"


def test_versioned_base_url_should_ignore_trailing_slash() -> None:
    # Given
    base_url = Url("https://api.tracker.com/")

    # When
    settings = ConcreteApiBasedIssueTrackerSettings(
        base_url=base_url,
        private_token="dummy_token",
        api_version="v2/",
    )

    # Then
    assert settings.versioned_base_url == "https://api.tracker.com/v2"


def test_versioned_base_url_should_ignore_trailing_slash_with_no_version() -> None:
    # Given
    base_url = Url("https://api.tracker.com/")

    # When
    settings = ConcreteApiBasedIssueTrackerSettings(
        base_url=base_url,
        private_token="dummy_token",
    )

    # Then
    assert settings.versioned_base_url == "https://api.tracker.com"
