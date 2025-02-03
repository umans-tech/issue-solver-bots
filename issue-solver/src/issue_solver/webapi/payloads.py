from typing import Literal

from anthropic.types import MessageParam
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field

from issue_solver.agents.coding_agent import Message
from issue_solver.models.supported_models import (
    SupportedOpenAIModel,
    SupportedAnthropicModel,
    QualifiedAIModel,
)


class OpenAIAgentResolutionSettings(BaseModel):
    agent: Literal["openai-tools"] = "openai-tools"
    model: QualifiedAIModel[SupportedOpenAIModel] = QualifiedAIModel(
        ai_model=SupportedOpenAIModel.GPT4O_MINI
    )
    history: list[ChatCompletionMessageParam | Message] | None = Field(
        default=None,
        description="Allows for resuming a resolution that was not completed",
    )


class AnthropicAgentResolutionSettings(BaseModel):
    agent: Literal["anthropic-tools"] = "anthropic-tools"
    model: QualifiedAIModel[SupportedAnthropicModel] = QualifiedAIModel(
        ai_model=SupportedAnthropicModel.CLAUDE_35_HAIKU, version="latest"
    )
    history: list[MessageParam | Message] | None = Field(
        default=None,
        description="Allows for resuming a resolution that was not completed",
    )


ResolutionSettings = OpenAIAgentResolutionSettings | AnthropicAgentResolutionSettings


class IterateIssueResolutionRequest(BaseModel):
    repo_location: str
    issue_description: str
    settings: ResolutionSettings = OpenAIAgentResolutionSettings(
        model=QualifiedAIModel(ai_model=SupportedOpenAIModel.GPT4O_MINI)
    )


class SolveIssueRequest(BaseModel):
    repo_location: str
    issue_description: str
    settings: ResolutionSettings
    max_iter: int = 10
