import os

from pydantic_core import Url

from issue_solver.issue_trackers.gitlab.settings import (
    GitlabIssueTrackerSettings,
    GitlabObjectType,
)


def test_gitlab_issue_tracker_minimal_valid_settings_with_default_values() -> None:
    # Given
    private_tocken = "my-s3cr3t-t0k3n"
    project_id = "182753"
    os.environ.clear()
    os.environ["GITLAB_PRIVATE_TOKEN"] = private_tocken
    os.environ["GITLAB_PROJECT_ID"] = project_id

    # When
    issue_tracker_settings = GitlabIssueTrackerSettings()

    # Then
    assert issue_tracker_settings.private_token == private_tocken
    assert issue_tracker_settings.project_id == project_id
    assert issue_tracker_settings.base_url == Url("https://gitlab.com")
    assert issue_tracker_settings.api_version == "4"
    assert issue_tracker_settings.object_type == GitlabObjectType.ISSUE


def test_gitlab_issue_tracker_full_valid_settings() -> None:
    # Given
    private_token = "my-s3cr3t-t0k3n-2"
    project_id = "9862693"
    gitlab_base_url = "https://gitlab.abccorp.com"
    gitlab_api_version = "3"
    os.environ.clear()
    os.environ["GITLAB_PRIVATE_TOKEN"] = private_token
    os.environ["GITLAB_PROJECT_ID"] = project_id
    os.environ["GITLAB_BASE_URL"] = gitlab_base_url
    os.environ["GITLAB_API_VERSION"] = gitlab_api_version
    os.environ["GITLAB_OBJECT_TYPE"] = "MR"

    # When
    issue_tracker_settings = GitlabIssueTrackerSettings()

    # Then
    assert issue_tracker_settings.private_token == private_token
    assert issue_tracker_settings.project_id == project_id
    assert issue_tracker_settings.base_url == Url(gitlab_base_url)
    assert issue_tracker_settings.api_version == gitlab_api_version
    assert issue_tracker_settings.object_type == GitlabObjectType.MR
