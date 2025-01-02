from dataclasses import dataclass
from enum import StrEnum


class AgentModel(StrEnum):
    GPT4O = "gpt-4o"
    GPT4O_MINI = "gpt-4o-mini"
    DEEPSEEK = "deepseek-coder"
    CLAUDE_35_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_35_HAIKU = "claude-3-5-haiku-20241022"
    QWEN25_CODER = "qwen2.5-coder"


class SupportedOpenAPIModel(StrEnum):
    GPT4O = "gpt-4o"
    GPT4O_MINI = "gpt-4o-mini"


class SupportedAnthropicModel(StrEnum):
    CLAUDE_35_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_35_HAIKU = "claude-3-5-haiku-20241022"


class SupportedDeepSeekModel(StrEnum):
    DEEPSEEK_Coder = "deepseek-coder"


class SupportedQwenModel(StrEnum):
    QWEN25_CODER = "qwen2.5-coder"


SupportedLLMModel = (
    SupportedOpenAPIModel
    | SupportedAnthropicModel
    | SupportedDeepSeekModel
    | SupportedQwenModel
)


class SupportedAgent(StrEnum):
    SWE_AGENT = "swe-agent"
    SWE_CRAFTER = "swe-crafter"


class IssueDescription(str):
    pass


@dataclass(frozen=True, kw_only=True)
class SolveIssueCommand:
    model: SupportedLLMModel
    agent: SupportedAgent
    issue_description: IssueDescription
