from enum import StrEnum
from typing import assert_never

from issue_solver.agents.agent_message_store import AgentMessageStore
from issue_solver.agents.anthropic_agent import AnthropicAgent
from issue_solver.agents.claude_code_agent import ClaudeCodeAgent
from issue_solver.agents.issue_resolving_agent import IssueResolvingAgent
from issue_solver.agents.openai_agent import OpenAIAgent
from issue_solver.agents.swe_agents_on_docker import (
    SweAgentOnDocker,
    SweCrafterOnDocker,
)
from issue_solver.models.model_settings import ModelSettings, AnthropicSettings


class SupportedAgent(StrEnum):
    SWE_AGENT = "swe-agent"
    SWE_CRAFTER = "swe-crafter"
    OPENAI_TOOLS = "openai-tools"
    ANTHROPIC_TOOLS = "anthropic-tools"
    CLAUDE_CODE = "claude-code"

    @classmethod
    def get(
        cls,
        agent: "SupportedAgent",
        *ai_models_settings: ModelSettings,
        agent_messages: AgentMessageStore | None = None,
    ) -> IssueResolvingAgent:
        match agent:
            case cls.SWE_AGENT:
                return SweAgentOnDocker(*ai_models_settings)
            case cls.SWE_CRAFTER:
                return SweCrafterOnDocker(*ai_models_settings)
            case cls.OPENAI_TOOLS:
                return OpenAIAgent(
                    api_key=ai_models_settings[0].api_key,
                    base_url=str(ai_models_settings[0].base_url),
                )
            case cls.ANTHROPIC_TOOLS:
                return AnthropicAgent(
                    api_key=ai_models_settings[0].api_key,
                    base_url=str(ai_models_settings[0].base_url),
                )
            case cls.CLAUDE_CODE:
                model_settings = ai_models_settings[0]
                if not isinstance(model_settings, AnthropicSettings):
                    raise ValueError(
                        f"Claude Code Agent requires AnthropicSettings for model settings, "
                        f"but {model_settings.__class__.__name__} were provided."
                    )
                return ClaudeCodeAgent(
                    api_key=model_settings.api_key,
                    agent_messages=agent_messages,
                )
            case _:
                assert_never(agent)
