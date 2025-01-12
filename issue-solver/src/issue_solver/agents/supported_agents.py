from enum import StrEnum
from typing import assert_never

from issue_solver.agents.issue_resolving_agent import IssueResolvingAgent
from issue_solver.agents.swe_agents_on_docker import (
    SweAgentOnDocker,
    SweCrafterOnDocker,
)
from issue_solver.models.model_settings import ModelSettings


class SupportedAgent(StrEnum):
    SWE_AGENT = "swe-agent"
    SWE_CRAFTER = "swe-crafter"
    OPENAI_TOOLS = "openai-tools"
    ANTHROPIC_TOOLS = "anthropic-tools"

    @classmethod
    def get(
        cls, agent: "SupportedAgent", *ai_models_settings: ModelSettings
    ) -> IssueResolvingAgent:
        match agent:
            case cls.SWE_AGENT:
                return SweAgentOnDocker(*ai_models_settings)
            case cls.SWE_CRAFTER:
                return SweCrafterOnDocker(*ai_models_settings)
            case cls.OPENAI_TOOLS:
                raise NotImplementedError(f"Agent {agent} is not implemented yet.")
            case cls.ANTHROPIC_TOOLS:
                raise NotImplementedError(f"Agent {agent} is not implemented yet.")
            case _:
                assert_never(agent)
