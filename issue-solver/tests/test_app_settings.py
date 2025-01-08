import os
from pathlib import Path

from pydantic_core import Url

from issue_solver import SupportedAgent, IssueInfo
from issue_solver.app_settings import IssueSettings, AppSettings
from issue_solver.issue_trackers.gitlab.settings import GitlabIssueTrackerSettings
from issue_solver.issue_trackers.issue_tracker import IssueInternalId
from issue_solver.models.model_settings import (
    AnthropicSettings,
)
from issue_solver.models.supported_models import (
    SupportedOpenAIModel,
)


def test_minimal_valid_app_settings_with_default_values() -> None:
    # Given
    os.environ.clear()

    git_access_token = "s3cr3t-t0k3n-for-git-ops"
    issue_description = "This is an actual description of the issue to be solved"
    os.environ["GIT__ACCESS_TOKEN"] = git_access_token
    os.environ["ISSUE__DESCRIPTION"] = issue_description

    # When
    app_settings = AppSettings()

    # Then
    assert app_settings.issue == IssueInfo(description=issue_description)
    assert app_settings.agent == SupportedAgent.SWE_AGENT
    assert app_settings.ai_model == SupportedOpenAIModel.GPT4O_MINI
    assert app_settings.selected_ai_model == str(SupportedOpenAIModel.GPT4O_MINI)
    assert app_settings.git.access_token == git_access_token


def test_full_valid_app_settings_with_gitlab_swe_crafter_and_anthropic() -> None:
    # Given
    gitlab_private_token = "my-s3cr3t-t0k3n"
    gitlab_project_id = "182753"
    issue_internal_id = "123"
    git_access_token = "s3cr3t-t0k3n-for-git-ops"
    git_user_mail = "bg@umans.tech"
    git_user_name = "bg"
    selected_agent = "swe-crafter"
    model = "claude-3-5-sonnet"
    model_version = "20241022"
    selected_model = "claude-3-5-sonnet-20241022"
    path_to_repo = "/path/to/repo"
    anthropic_api_key = "my-anthropic-api-key"
    anthropic_base_url = "https://api.antropic.mycorp.com"

    os.environ.clear()
    os.environ["ISSUE__TRACKER__TYPE"] = "GITLAB"
    os.environ["ISSUE__TRACKER__PRIVATE_TOKEN"] = gitlab_private_token
    os.environ["ISSUE__REF__PROJECT_ID"] = gitlab_project_id
    os.environ["ISSUE__REF__IID"] = issue_internal_id
    os.environ["AGENT"] = selected_agent
    os.environ["AI_MODEL"] = model
    os.environ["AI_MODEL_VERSION"] = model_version
    os.environ["REPO_PATH"] = path_to_repo
    os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key
    os.environ["ANTHROPIC_BASE_URL"] = anthropic_base_url
    os.environ["GIT__ACCESS_TOKEN"] = git_access_token
    os.environ["GIT__USER_MAIL"] = git_user_mail
    os.environ["GIT__USER_NAME"] = git_user_name

    # When
    app_settings = AppSettings()

    # Then
    selected_issue_tracker = app_settings.selected_issue_tracker
    assert type(selected_issue_tracker) is GitlabIssueTrackerSettings
    assert selected_issue_tracker.private_token == gitlab_private_token
    assert selected_issue_tracker.base_url == Url("https://gitlab.com")

    assert type(app_settings.issue) is IssueSettings
    assert app_settings.issue.ref == IssueInternalId(
        project_id=gitlab_project_id, iid=issue_internal_id
    )
    assert app_settings.agent == selected_agent
    assert app_settings.selected_ai_model == selected_model
    assert app_settings.git.access_token == git_access_token
    assert app_settings.git.user_mail == git_user_mail
    assert app_settings.git.user_name == git_user_name
    assert app_settings.repo_path == Path(path_to_repo)
    assert app_settings.model_settings == AnthropicSettings(
        api_key=anthropic_api_key, base_url=Url(anthropic_base_url)
    )
