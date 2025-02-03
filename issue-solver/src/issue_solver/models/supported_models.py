from dataclasses import dataclass
from enum import StrEnum
from typing import TypeVar, Generic


class SupportedOpenAIModel(StrEnum):
    GPT4O = "gpt-4o"
    GPT4O_MINI = "gpt-4o-mini"


class SupportedAnthropicModel(StrEnum):
    CLAUDE_35_SONNET = "claude-3-5-sonnet"
    CLAUDE_35_HAIKU = "claude-3-5-haiku"


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
