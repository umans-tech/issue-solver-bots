from pathlib import Path
from typing import assert_never

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from issue_solver.agents.issue_resolving_agent import (
    VersionedAIModelWithSettings,
)
from issue_solver.agents.supported_agents import SupportedAgent
from issue_solver.git_operations.git_helper import GitSettings
from issue_solver.issues.issue import IssueInfo
from issue_solver.issues.trackers.supported_issue_trackers import (
    IssueSourceSettings,
)
from issue_solver.issues.issue_settings import IssueSettings
from issue_solver.models.model_settings import (
    ModelSettings,
    OpenAISettings,
    DeepSeekSettings,
    AnthropicSettings,
    QwenSettings,
)
from issue_solver.models.supported_models import (
    SupportedOpenAIModel,
    SupportedAIModel,
    SupportedDeepSeekModel,
    SupportedAnthropicModel,
    SupportedQwenModel,
    VersionedAIModel,
)


class SolveCommandSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    issue: IssueInfo | IssueSettings = Field(
        description="Reference to the issue "
        "(url, id, iid+project_id or anything that allow the issue tracker to find the issue) "
        "or actual Content describing the issue"
    )
    agent: SupportedAgent = Field(
        default=SupportedAgent.SWE_AGENT,
        description="Which agent to use: e.g. swe-agent or swe-crafter.",
    )
    ai_model: SupportedAIModel = Field(
        default=SupportedOpenAIModel.GPT4O_MINI,
        description="Which model to use for the issue solving.",
    )
    ai_model_version: str | None = Field(
        default=None,
        description="Which version of the model to use for the issue solving.",
    )
    git: GitSettings = Field(description="Git settings.")
    repo_path: Path = Field(
        default=Path("."),
        description="Path to the repository where the issue is located.",
    )
    process_id: str | None = Field(
        default=None,
        description="Process ID for the issue solving. If not provided, a new UUID will be generated",
    )

    database_url: str | None = Field(
        default=None,
        description="Database URL for storing events and messages related to issue resolution process. If not provided, no database will be used.",
    )

    redis_url: str | None = Field(
        default=None,
        description="Redis URL to stream messages related to issue resolution process. If not provided, no Redis will be used.",
    )

    process_queue_url: str | None = Field(
        default=None,
        description="SQS Queue URL to stream messages related to issue resolution process. If not provided, no SQS will be used.",
    )

    @property
    def selected_issue_tracker(self) -> IssueSourceSettings | None:
        if isinstance(self.issue, IssueSettings):
            return self.issue.tracker
        return None

    @property
    def model_settings(self) -> ModelSettings:
        match self.ai_model:
            case SupportedOpenAIModel():
                return OpenAISettings()
            case SupportedDeepSeekModel():
                return DeepSeekSettings()
            case SupportedAnthropicModel():
                return AnthropicSettings()
            case SupportedQwenModel():
                return QwenSettings()
            case _:
                assert_never(self.ai_model)

    @property
    def selected_ai_model(self) -> str:
        return str(self.versioned_ai_model)

    @property
    def versioned_ai_model(self) -> VersionedAIModel:
        return VersionedAIModel(ai_model=self.ai_model, version=self.ai_model_version)

    @property
    def selected_model_with_settings(self) -> VersionedAIModelWithSettings:
        return VersionedAIModelWithSettings(
            model=self.versioned_ai_model, settings=self.model_settings
        )
