from dataclasses import dataclass
from enum import StrEnum
from typing import TypeVar, Generic


class SupportedOpenAIModel(StrEnum):
    GPT4O = "gpt-4o"
    GPT5 = "gpt-5"
    GPT4O_MINI = "gpt-4o-mini"
    GPT5_MINI = "gpt-5-mini"
    GPT41 = "gpt-4.1"
    GPT41_MINI = "gpt-4.1-mini"
    GPT41_NANO = "gpt-4.1-nano"


class SupportedAnthropicModel(StrEnum):
    CLAUDE_35_SONNET = "claude-3-5-sonnet"
    CLAUDE_35_HAIKU = "claude-3-5-haiku"
    CLAUDE_37_SONNET = "claude-3-7-sonnet"
    CLAUDE_SONNET_4 = "claude-sonnet-4"
    CLAUDE_OPUS_4 = "claude-opus-4"


LATEST_CLAUDE_4_VERSION = "20250514"


class SupportedDeepSeekModel(StrEnum):
    DEEPSEEK_Coder = "deepseek-coder"


class SupportedQwenModel(StrEnum):
    QWEN25_CODER = "qwen2.5-coder"


SupportedAIModel = (
    SupportedOpenAIModel
    | SupportedAnthropicModel
    | SupportedDeepSeekModel
    | SupportedQwenModel
)

ModelT = TypeVar("ModelT", bound=SupportedAIModel)


@dataclass(frozen=True)
class QualifiedAIModel(Generic[ModelT]):
    ai_model: ModelT
    version: str | None = None

    def __repr__(self):
        if self.version:
            return f"{self.ai_model.value}-{self.version}"
        return self.ai_model.value


VersionedAIModel = QualifiedAIModel[SupportedAIModel]
