from enum import StrEnum
from typing import Self

from issue_solver.agents.issue_resolving_agent import IssueResolvingAgent


class SupportedAgent(StrEnum):
    SWE_AGENT = "swe-agent"
    SWE_CRAFTER = "swe-crafter"
    OPENAI_TOOLS = "openai-tools"
    ANTHROPIC_TOOLS = "anthropic-tools"

    @classmethod
    def get(cls, agent: Self) -> IssueResolvingAgent:
        raise NotImplementedError(" SupportedAgent.get is not implemented yet.")
