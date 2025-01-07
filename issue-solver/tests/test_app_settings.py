import os
from dataclasses import dataclass
from pathlib import Path
from typing import assert_never

from httpcore import URL
from pydantic import Field
from pydantic_core import Url
from pydantic_settings import BaseSettings, SettingsConfigDict

from issue_solver import SupportedAgent, IssueInfo
from issue_solver.git_operations.git_helper import GitSettings
from issue_solver.issue_trackers.gitlab.settings import GitlabIssueTrackerSettings
from issue_solver.issue_trackers.supported_issue_trackers import IssueSourceSettings
from issue_solver.models.model_settings import (
    ModelSettings,
    AnthropicSettings,
    OpenAISettings,
    DeepSeekSettings,
    QwenSettings,
)
from issue_solver.models.supported_models import (
    SupportedLLMModel,
    SupportedOpenAPIModel,
    SupportedDeepSeekModel,
    SupportedAnthropicModel,
    SupportedQwenModel,
)


@dataclass
class IssueId:
    id: str


@dataclass
class IssueInternalId:
    project_id: str
    iid: str


IssueReference = IssueId | IssueInternalId | URL


@dataclass
class IssueSettings:
    tracker: IssueSourceSettings
    ref: IssueReference


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")

    issue: IssueInfo | IssueSettings = Field(
        description="Reference to the issue "
        "(url, id, iid+project_id or anything that allow the issue tracker to find the issue) "
        "or actual Content describing the issue"
    )
    agent: SupportedAgent = Field(
        default=SupportedAgent.SWE_AGENT,
        description="Which agent to use: e.g. swe-agent or swe-crafter.",
    )
    model: SupportedLLMModel = Field(
        default=SupportedOpenAPIModel.GPT4O_MINI,
        description="Which model to use for patch generation.",
    )
    git: GitSettings = Field(description="Git settings.")
    repo_path: Path = Field(
        default=Path("."),
        description="Path to the repository where the issue is located.",
    )

    @property
    def selected_issue_tracker(self) -> IssueSourceSettings | None:
        if isinstance(self.issue, IssueSettings):
            return self.issue.tracker
        return None

    @property
    def model_settings(self) -> ModelSettings:
        match self.model:
            case SupportedOpenAPIModel():
                return OpenAISettings()
            case SupportedDeepSeekModel():
                return DeepSeekSettings()
            case SupportedAnthropicModel():
                return AnthropicSettings()
            case SupportedQwenModel():
                return QwenSettings()
            case _:
                assert_never(self.model)


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
    assert app_settings.model == SupportedOpenAPIModel.GPT4O_MINI
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
    selected_model = "claude-3-5-sonnet-20241022"
    path_to_repo = "/path/to/repo"
    anthropic_api_key = "my-anthropic-api-key"
    anthropic_base_url = "https://api.antropic.mycorp.com"

    os.environ.clear()
    os.environ["ISSUE__TRACKER__PRIVATE_TOKEN"] = gitlab_private_token
    os.environ["ISSUE__TRACKER__PROJECT_ID"] = gitlab_project_id
    os.environ["ISSUE__REF__PROJECT_ID"] = gitlab_project_id
    os.environ["ISSUE__REF__IID"] = issue_internal_id
    os.environ["GIT__ACCESS_TOKEN"] = git_access_token
    os.environ["GIT__USER_MAIL"] = git_user_mail
    os.environ["GIT__USER_NAME"] = git_user_name
    os.environ["AGENT"] = selected_agent
    os.environ["MODEL"] = selected_model
    os.environ["REPO_PATH"] = path_to_repo
    os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key
    os.environ["ANTHROPIC_BASE_URL"] = anthropic_base_url

    # When
    app_settings = AppSettings()

    # Then
    selected_issue_tracker = app_settings.selected_issue_tracker
    assert type(selected_issue_tracker) is GitlabIssueTrackerSettings
    assert selected_issue_tracker.private_token == gitlab_private_token
    assert selected_issue_tracker.project_id == gitlab_project_id
    assert selected_issue_tracker.base_url == Url("https://gitlab.com")

    assert type(app_settings.issue) is IssueSettings
    assert app_settings.issue.ref == IssueInternalId(
        project_id=gitlab_project_id, iid=issue_internal_id
    )
    assert app_settings.agent == selected_agent
    assert app_settings.model == selected_model
    assert app_settings.git.access_token == git_access_token
    assert app_settings.git.user_mail == git_user_mail
    assert app_settings.git.user_name == git_user_name
    assert app_settings.repo_path == Path(path_to_repo)
    assert app_settings.model_settings == AnthropicSettings(
        api_key=anthropic_api_key, base_url=Url(anthropic_base_url)
    )
