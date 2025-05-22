import os

from pydantic import AnyUrl

from issue_solver.issues.trackers.gitlab_issue_tracker import (
    GitlabObjectType,
    GitlabIssueTracker,
)


def test_gitlab_issue_tracker_minimal_valid_settings_with_default_values() -> None:
    # Given
    private_tocken = "my-s3cr3t-t0k3n"
    os.environ.clear()
    os.environ["GITLAB_PRIVATE_TOKEN"] = private_tocken

    # When
    issue_tracker_settings = GitlabIssueTracker.Settings()

    # Then
    assert issue_tracker_settings.private_token == private_tocken
    assert issue_tracker_settings.base_url == AnyUrl("https://gitlab.com")
    assert issue_tracker_settings.api_version == "4"
    assert issue_tracker_settings.object_type == GitlabObjectType.ISSUE


def test_gitlab_issue_tracker_full_valid_settings() -> None:
    # Given
    private_token = "my-s3cr3t-t0k3n-2"
    gitlab_base_url = "https://gitlab.abccorp.com"
    gitlab_api_version = "3"
    os.environ.clear()
    os.environ["GITLAB_PRIVATE_TOKEN"] = private_token
    os.environ["GITLAB_BASE_URL"] = gitlab_base_url
    os.environ["GITLAB_API_VERSION"] = gitlab_api_version
    os.environ["GITLAB_OBJECT_TYPE"] = "MR"

    # When
    issue_tracker_settings = GitlabIssueTracker.Settings()

    # Then
    assert issue_tracker_settings.private_token == private_token
    assert issue_tracker_settings.base_url == AnyUrl(gitlab_base_url)
    assert issue_tracker_settings.api_version == gitlab_api_version
    assert issue_tracker_settings.object_type == GitlabObjectType.MR
