import os
import logging
from typing import assert_never
from starlette.requests import Request

from issue_solver.agents.coding_agent import CodingAgent
from issue_solver.agents.openai_agent import OpenAIAgent
from issue_solver.agents.anthropic_agent import AnthropicAgent
from issue_solver.events.in_memory_event_store import InMemoryEventStore
from issue_solver.webapi.payloads import ResolutionSettings

# Get logger for your module
logger = logging.getLogger("issue_solver.webapi.dependencies")
logger.setLevel(logging.INFO)

def get_event_store(request: Request) -> InMemoryEventStore:
    """Dependency to get the event store from the app state."""
    return request.app.state.event_store

def get_agent(setting: ResolutionSettings) -> CodingAgent:
    """Factory function to get the appropriate agent based on settings."""
    match setting.agent:
        case "openai-tools":
            return OpenAIAgent(api_key=os.environ["OPENAI_API_KEY"])
        case "anthropic-tools":
            return AnthropicAgent(
                api_key=os.environ["ANTHROPIC_API_KEY"],
            )
        case _:
            assert_never(setting.agent) 