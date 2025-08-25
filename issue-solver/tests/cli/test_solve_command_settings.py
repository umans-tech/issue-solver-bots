import os
from pathlib import Path

import pytest
from pydantic import ValidationError, AnyUrl

from issue_solver.agents.supported_agents import SupportedAgent
from issue_solver.cli.solve_command_settings import SolveCommandSettings
from issue_solver.issues.issue import IssueInternalId, IssueInfo
from issue_solver.issues.issue_settings import IssueSettings
from issue_solver.issues.trackers.azure_devops_issue_tracker import (
    AzureDevOpsIssueTracker,
)
from issue_solver.issues.trackers.github_issue_tracker import GithubIssueTracker
from issue_solver.issues.trackers.gitlab_issue_tracker import GitlabIssueTracker
from issue_solver.issues.trackers.http_based_issue_tracker import HttpBasedIssueTracker
from issue_solver.issues.trackers.jira_issue_tracker import JiraIssueTracker
from issue_solver.issues.trackers.notion_issue_tracker import NotionIssueTracker
from issue_solver.issues.trackers.trello_issue_tracker import TrelloIssueTracker
from issue_solver.models.model_settings import (
    AnthropicSettings,
    DeepSeekSettings,
    QwenSettings,
    OpenAISettings,
)
from issue_solver.models.supported_models import (
    SupportedOpenAIModel,
    SupportedDeepSeekModel,
    SupportedQwenModel,
    SupportedAnthropicModel,
)


@pytest.fixture
def clean_env() -> None:
    # to test in isolation and avoid side effects due to local env vars
    SolveCommandSettings.model_config["env_file"] = ""
    os.environ.clear()


def test_minimal_valid_app_settings_with_default_values(clean_env: None) -> None:
    # Given
    git_access_token = "s3cr3t-t0k3n-for-git-ops"
    issue_description = issue_description_example()
    os.environ["GIT__ACCESS_TOKEN"] = git_access_token
    os.environ["ISSUE__DESCRIPTION"] = issue_description
    os.environ["OPENAI_API_KEY"] = "openai-test-key"

    # When
    app_settings = SolveCommandSettings()

    # Then
    assert app_settings.issue == IssueInfo(description=issue_description)
    assert app_settings.agent == SupportedAgent.SWE_AGENT
    assert app_settings.ai_model == SupportedOpenAIModel.GPT4O_MINI
    assert app_settings.selected_ai_model == str(SupportedOpenAIModel.GPT4O_MINI)
    assert app_settings.git.access_token == git_access_token
    assert app_settings.model_settings == OpenAISettings(
        api_key="openai-test-key",
    )


def test_full_valid_app_settings_with_gitlab_swe_crafter_and_anthropic(
    clean_env: None,
) -> None:
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
    app_settings = SolveCommandSettings()

    # Then
    selected_issue_tracker = app_settings.selected_issue_tracker
    assert type(selected_issue_tracker) is GitlabIssueTracker.Settings
    assert selected_issue_tracker.private_token == gitlab_private_token
    assert selected_issue_tracker.base_url == AnyUrl("https://gitlab.com")

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
        api_key=anthropic_api_key, base_url=AnyUrl(anthropic_base_url)
    )


def test_openai_model_with_required_fields(clean_env: None) -> None:
    # Given
    os.environ["GIT__ACCESS_TOKEN"] = "my-git-token"
    os.environ["ISSUE__DESCRIPTION"] = "OpenAI model usage"
    os.environ["OPENAI_API_KEY"] = "openai-test-key"
    os.environ["AI_MODEL"] = SupportedOpenAIModel.GPT4O

    # When
    app_settings = SolveCommandSettings()
    model_settings = app_settings.model_settings

    # Then
    assert app_settings.ai_model == SupportedOpenAIModel.GPT4O
    assert isinstance(model_settings, OpenAISettings)
    assert model_settings.api_key == "openai-test-key"


def test_deepseek_model_with_required_fields(clean_env: None) -> None:
    # Given
    os.environ["GIT__ACCESS_TOKEN"] = "my-git-token"
    os.environ["ISSUE__DESCRIPTION"] = "DeepSeek model usage"
    os.environ["AI_MODEL"] = SupportedDeepSeekModel.DEEPSEEK_Coder
    os.environ["DEEPSEEK_API_KEY"] = "deepseek-key"

    # When
    app_settings = SolveCommandSettings()
    model_settings = app_settings.model_settings

    # Then
    assert isinstance(app_settings.ai_model, SupportedDeepSeekModel)
    assert isinstance(model_settings, DeepSeekSettings)
    assert model_settings.api_key == "deepseek-key"


def test_anthropic_model_with_required_fields(clean_env: None) -> None:
    # Given
    os.environ["GIT__ACCESS_TOKEN"] = "my-git-token"
    os.environ["ISSUE__DESCRIPTION"] = "Anthropic model usage"
    os.environ["AI_MODEL"] = SupportedAnthropicModel.CLAUDE_35_HAIKU
    os.environ["AI_MODEL_VERSION"] = "20250110"
    os.environ["ANTHROPIC_API_KEY"] = "anthropic-test-key"
    os.environ["ANTHROPIC_BASE_URL"] = "https://api.anthropic.example.org"

    # When
    app_settings = SolveCommandSettings()
    model_settings = app_settings.model_settings

    # Then
    assert app_settings.ai_model == SupportedAnthropicModel.CLAUDE_35_HAIKU
    assert isinstance(model_settings, AnthropicSettings)
    assert model_settings.api_key == "anthropic-test-key"
    assert model_settings.base_url == AnyUrl("https://api.anthropic.example.org")


def test_qwen_model_with_required_fields(clean_env: None) -> None:
    # Given
    os.environ["GIT__ACCESS_TOKEN"] = "my-git-token"
    os.environ["ISSUE__DESCRIPTION"] = "Qwen model usage"
    os.environ["AI_MODEL"] = SupportedQwenModel.QWEN25_CODER
    os.environ["QWEN_API_KEY"] = "qwen-test-key"

    # When
    app_settings = SolveCommandSettings()
    model_settings = app_settings.model_settings

    # Then
    assert isinstance(app_settings.ai_model, SupportedQwenModel)
    assert isinstance(model_settings, QwenSettings)
    assert model_settings.api_key == "qwen-test-key"


def test_issue_settings_gitlab_tracker(clean_env: None) -> None:
    # Given
    os.environ["GIT__ACCESS_TOKEN"] = "my-git-token"
    os.environ["ISSUE__TRACKER__TYPE"] = "GITLAB"
    os.environ["ISSUE__TRACKER__PRIVATE_TOKEN"] = "my-gitlab-private-token"
    os.environ["ISSUE__REF__PROJECT_ID"] = "999"
    os.environ["ISSUE__REF__IID"] = "888"

    # When
    app_settings = SolveCommandSettings()

    # Then
    assert isinstance(app_settings.issue, IssueSettings)
    assert isinstance(app_settings.selected_issue_tracker, GitlabIssueTracker.Settings)
    assert (
        app_settings.selected_issue_tracker.private_token == "my-gitlab-private-token"
    )
    assert isinstance(app_settings.issue.ref, IssueInternalId)
    assert app_settings.issue.ref.project_id == "999"
    assert app_settings.issue.ref.iid == "888"


def test_issue_info_no_tracker(clean_env: None) -> None:
    # Given
    os.environ["GIT__ACCESS_TOKEN"] = "my-git-token"
    os.environ["ISSUE__DESCRIPTION"] = "Some plain description"

    # When
    app_settings = SolveCommandSettings()

    # Then
    assert isinstance(app_settings.issue, IssueInfo)
    assert app_settings.issue.description == "Some plain description"
    assert app_settings.selected_issue_tracker is None


def test_custom_repo_path(clean_env: None) -> None:
    # Given
    os.environ["GIT__ACCESS_TOKEN"] = "my-git-token"
    os.environ["ISSUE__DESCRIPTION"] = "Check custom repo path"
    os.environ["REPO_PATH"] = "/custom/repo/path"

    # When
    app_settings = SolveCommandSettings()

    # Then
    assert app_settings.repo_path == Path("/custom/repo/path")


def test_invalid_model_raises_validation_error(clean_env: None) -> None:
    # Given
    os.environ["GIT__ACCESS_TOKEN"] = "test-token"
    os.environ["ISSUE__DESCRIPTION"] = "Invalid model usage"
    os.environ["AI_MODEL"] = "some-nonexistent-model"

    # When / Then
    with pytest.raises(ValidationError):
        _ = SolveCommandSettings()


def test_incomplete_tracker_info_raises_error(clean_env: None) -> None:
    # Given
    os.environ["GIT__ACCESS_TOKEN"] = "test-token"
    os.environ["ISSUE__REF__PROJECT_ID"] = "999"
    os.environ["ISSUE__REF__IID"] = "888"

    # When / Then
    with pytest.raises(ValidationError):
        _ = SolveCommandSettings()


def test_selected_model_with_settings(clean_env: None) -> None:
    # Given
    os.environ["GIT__ACCESS_TOKEN"] = "test-token"
    os.environ["ISSUE__DESCRIPTION"] = "Check selected model with settings"
    os.environ["AI_MODEL"] = SupportedAnthropicModel.CLAUDE_35_SONNET
    os.environ["AI_MODEL_VERSION"] = "20250110"
    os.environ["ANTHROPIC_API_KEY"] = "anthropic-test-key"
    os.environ["ANTHROPIC_BASE_URL"] = "https://api.anthropic.example.org"

    # When
    app_settings = SolveCommandSettings()
    model_with_settings = app_settings.selected_model_with_settings

    # Then
    assert (
        model_with_settings.model.ai_model == SupportedAnthropicModel.CLAUDE_35_SONNET
    )
    assert model_with_settings.model.version == "20250110"
    assert isinstance(model_with_settings.settings, AnthropicSettings)
    assert model_with_settings.settings.api_key == "anthropic-test-key"
    assert model_with_settings.settings.base_url == AnyUrl(
        "https://api.anthropic.example.org"
    )


def test_github_tracker_is_interpreted_correctly(clean_env: None) -> None:
    # Given
    os.environ["ISSUE__TRACKER__TYPE"] = "GITHUB"
    os.environ["ISSUE__REF__PROJECT_ID"] = "octocat/Hello-World"
    os.environ["ISSUE__REF__IID"] = "101"
    os.environ["GIT__ACCESS_TOKEN"] = "some-git-access-token"

    # When
    app_settings = SolveCommandSettings()

    # Then
    assert isinstance(app_settings.issue, IssueSettings)
    tracker = app_settings.selected_issue_tracker
    assert isinstance(tracker, GithubIssueTracker.Settings)
    assert tracker.type == "GITHUB"
    assert tracker.base_url == AnyUrl("https://api.github.com")
    assert isinstance(app_settings.issue.ref, IssueInternalId)
    assert app_settings.issue.ref.project_id == "octocat/Hello-World"
    assert app_settings.issue.ref.iid == "101"


def test_jira_tracker_is_interpreted_correctly(clean_env: None) -> None:
    # Given
    os.environ["ISSUE__TRACKER__TYPE"] = "JIRA"
    os.environ["ISSUE__REF__PROJECT_ID"] = "JIR"
    os.environ["ISSUE__REF__IID"] = "2023"
    os.environ["GIT__ACCESS_TOKEN"] = "some-git-access-token"

    # When
    app_settings = SolveCommandSettings()

    # Then
    assert isinstance(app_settings.issue, IssueSettings)
    tracker = app_settings.selected_issue_tracker
    assert isinstance(tracker, JiraIssueTracker.Settings)
    assert tracker.type == "JIRA"


def test_trello_tracker_is_interpreted_correctly(clean_env: None) -> None:
    # Given
    os.environ["ISSUE__TRACKER__TYPE"] = "TRELLO"
    os.environ["ISSUE__TRACKER__API_KEY"] = "my-trello-api-key"
    os.environ["ISSUE__TRACKER__PRIVATE_TOKEN"] = "my-trello-private-token"
    os.environ["ISSUE__REF__PROJECT_ID"] = "my-trello-board"
    os.environ["ISSUE__REF__IID"] = "42"
    os.environ["GIT__ACCESS_TOKEN"] = "some-git-access-token"

    # When
    app_settings = SolveCommandSettings()

    # Then
    assert isinstance(app_settings.issue, IssueSettings)
    tracker = app_settings.selected_issue_tracker
    assert isinstance(tracker, TrelloIssueTracker.Settings)
    assert tracker.type == "TRELLO"


def test_azure_devops_tracker_is_interpreted_correctly(clean_env: None) -> None:
    # Given
    os.environ["ISSUE__TRACKER__TYPE"] = "AZURE_DEVOPS"
    os.environ["ISSUE__REF__PROJECT_ID"] = "my-azure-org/my-azure-project"
    os.environ["ISSUE__REF__IID"] = "987"
    os.environ["GIT__ACCESS_TOKEN"] = "some-git-access-token"

    # When
    app_settings = SolveCommandSettings()

    # Then
    assert isinstance(app_settings.issue, IssueSettings)
    tracker = app_settings.selected_issue_tracker
    assert isinstance(tracker, AzureDevOpsIssueTracker.Settings)
    assert tracker.type == "AZURE_DEVOPS"


def test_http_based_tracker_is_interpreted_correctly(clean_env: None) -> None:
    # Given
    os.environ["ISSUE__TRACKER__TYPE"] = "HTTP"
    os.environ["ISSUE__TRACKER__BASE_URL"] = "https://my-http-service.example.org"
    os.environ["ISSUE__REF__PROJECT_ID"] = "my-http-service"
    os.environ["ISSUE__REF__IID"] = "42"
    os.environ["GIT__ACCESS_TOKEN"] = "some-git-access-token"

    # When
    app_settings = SolveCommandSettings()

    # Then
    assert isinstance(app_settings.issue, IssueSettings)
    tracker = app_settings.selected_issue_tracker
    assert isinstance(tracker, HttpBasedIssueTracker.Settings)
    assert tracker.type == "HTTP"
    assert tracker.base_url == AnyUrl("https://my-http-service.example.org")


def test_notion_tracker_is_interpreted_correctly(clean_env: None) -> None:
    # Given
    os.environ["ISSUE__TRACKER__TYPE"] = "NOTION"
    os.environ["ISSUE__TRACKER__PRIVATE_TOKEN"] = "my-notion-private-token"
    os.environ["ISSUE__REF__PROJECT_ID"] = "someWorkspace"
    os.environ["ISSUE__REF__IID"] = "notion-page-id"
    os.environ["GIT__ACCESS_TOKEN"] = "some-git-access-token"

    # When
    app_settings = SolveCommandSettings()

    # Then
    assert isinstance(app_settings.issue, IssueSettings)
    tracker = app_settings.selected_issue_tracker
    assert isinstance(tracker, NotionIssueTracker.Settings)
    assert tracker.type == "NOTION"
    assert tracker.base_url == AnyUrl("https://api.notion.com/v1")


def issue_description_example() -> str:
    return "This is an actual description of the issue to be solved"
