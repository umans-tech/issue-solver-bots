from pathlib import Path
from typing import assert_never

from pydantic import Field, AnyUrl
from pydantic_settings import BaseSettings

from issue_solver import SupportedAgent
from issue_solver.agents.issue_resolving_agent import IssueDescription
from issue_solver.git_operations.git_helper import GitSettings
from issue_solver.issue_trackers import SupportedIssueTracker
from issue_solver.models.model_settings import (
    ModelSettings,
    OpenAISettings,
    DeepSeekSettings,
    AnthropicSettings,
    QwenSettings,
)
from issue_solver.models.supported_models import (
    SupportedOpenAPIModel,
    SupportedLLMModel,
    SupportedDeepSeekModel,
    SupportedAnthropicModel,
    SupportedQwenModel,
)


class AppSettings(BaseSettings):
    repo_path: Path | None = Field(
        default=".", description="Path to the repository where the issue is located."
    )
    ci_merge_request_iid: str | None = Field(
        default=None,
        alias="CI_MERGE_REQUEST_IID",
        description="Merge Request IID, if running in a GitLab MR pipeline.",
    )
    ci_merge_request_description: str | None = Field(
        default=None,
        alias="CI_MERGE_REQUEST_DESCRIPTION",
        description="Merge Request description text.",
    )
    ci_merge_request_title: str | None = Field(
        default=None, alias="CI_MERGE_REQUEST_TITLE", description="Merge Request title."
    )

    # Issue variables (GitLab/GitHub/Jira/etc.)
    gitlab_issue_id: str | None = Field(
        default=None,
        alias="GITLAB_ISSUE_ID",
        description="GitLab issue ID if running in issue mode.",
    )
    issue_url: AnyUrl | None = Field(
        default=None,
        alias="ISSUE_URL",
        description="If set, used as the data_path or direct reference to an external issue.",
    )
    issue_description: IssueDescription | None = Field(
        default=None,
        alias="ISSUE_DESCRIPTION",
        description="Content describing the issue (manual trigger).",
    )

    # Agent & model selection
    agent: SupportedAgent = Field(
        default=SupportedAgent.SWE_AGENT,
        alias="AGENT",
        description="Which agent to use: e.g. swe-agent or swe-crafter.",
    )
    model_name: SupportedLLMModel = Field(
        default=SupportedOpenAPIModel.GPT4O_MINI,
        alias="MODEL_NAME",
        description="Which model to use for patch generation.",
    )

    # Access tokens / credentials
    coding_agent_access_token: str | None = Field(
        default=None,
        alias="CODING_AGENT_ACCESS_TOKEN",
        description="Token used for GitLab push or other authenticated calls.",
    )
    openai_api_key: str | None = Field(
        default=None,
        alias="OPENAI_API_KEY",
        description="OpenAI API key, if referencing OpenAI-based models.",
    )
    deepseek_api_key: str | None = Field(
        default=None,
        alias="DEEPSEEK_API_KEY",
        description="API key for DeepSeek coder.",
    )

    # Additional environment variables
    deepseek_api_base_url: AnyUrl | None = Field(
        default=None,
        alias="DEEPSEEK_API_BASE_URL",
        description="Base URL for the DeepSeek coder API.",
    )
    ci_project_id: str | None = Field(
        default=None,
        alias="CI_PROJECT_ID",
        description="GitLab project ID used when fetching issues via API.",
    )
    ci_project_url: AnyUrl | None = Field(
        default=None,
        alias="CI_PROJECT_URL",
        description="GitLab project URL used for 'git remote add' operations.",
    )
    ci_commit_ref_name: str | None = Field(
        default=None,
        alias="CI_COMMIT_REF_NAME",
        description="Commit reference name (branch) used in pipelines.",
    )

    @property
    def selected_issue_tracker(self) -> SupportedIssueTracker | None:
        if self.gitlab_issue_id:
            return SupportedIssueTracker.GITLAB
        if self.ci_merge_request_iid:
            return SupportedIssueTracker.GITLAB_MR
        if self.issue_url:
            return SupportedIssueTracker.URL_BASED
        return None

    @property
    def git_settings(self) -> "GitSettings":
        return GitSettings(
            coding_agent_access_token=self.coding_agent_access_token,
            agent_git_user_mail=self.agent_git_user_mail,
            agent_git_user_name=self.agent_git_user_name,
        )

    @property
    def model_settings(self) -> ModelSettings:
        match self.model_name:
            case SupportedOpenAPIModel():
                return OpenAISettings()
            case SupportedDeepSeekModel():
                return DeepSeekSettings()
            case SupportedAnthropicModel():
                return AnthropicSettings()
            case SupportedQwenModel():
                return QwenSettings()
            case _:
                assert_never(self.model_name)

    class Config:
        env_prefix = ""  # Read environment vars as is
        env_file = ".env"  # Optional: load from .env
        env_file_encoding = "utf-8"
