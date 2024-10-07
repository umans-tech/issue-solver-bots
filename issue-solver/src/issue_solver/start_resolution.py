from dataclasses import dataclass
from enum import Enum


class AgentModel(Enum):
    GPT4O = "gpt-4o"
    GPT4O_MINI = "gpt-4o-mini"
    DEEPSEEK = "deepseek-coder"
    CLAUDE_35_SONNET = "claude-3.5-sonnet"
    CLAUDE_35_HAIKU = "claude-3.5-haiku"
    QWEN25_CODER = "qwen2.5-coder"


class AgentName(Enum):
    SWE_AGENT = "swe-agent"
    SWE_CRAFTER = "swe-crafter"


class IssueDescription(str):
    pass


@dataclass(frozen=True, kw_only=True)
class SolveIssueCommand:
    agent_model: AgentModel
    agent_name: AgentName
    issue_description: IssueDescription
