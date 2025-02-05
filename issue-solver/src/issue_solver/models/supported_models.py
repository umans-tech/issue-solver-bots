from enum import StrEnum


class AgentModel(StrEnum):
    GPT4O = "gpt-4o"
    GPT4O_MINI = "gpt-4o-mini"
    DEEPSEEK = "deepseek-coder"
    CLAUDE_35_SONNET = "claude-3-5-sonnet"
    CLAUDE_35_HAIKU = "claude-3-5-haiku"
    QWEN25_CODER = "qwen2.5-coder"


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
