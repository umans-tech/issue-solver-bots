from issue_solver.agents.supported_agents import SupportedAgent
from issue_solver.agents.swe_agents_on_docker import (
    SweAgentOnDocker,
    SweCrafterOnDocker,
)
from issue_solver.models.model_settings import OpenAISettings


def test_supported_agent_get_swe_agent() -> None:
    # Arrange
    open_ai_settings = OpenAISettings(
        api_key="s3cr3t-k3y",
    )
    # Act
    agent = SupportedAgent.get(
        SupportedAgent.SWE_AGENT,
        open_ai_settings,
    )
    # Assert
    assert isinstance(agent, SweAgentOnDocker)
    assert agent.env_vars.get("OPENAI_API_KEY") == "s3cr3t-k3y"


def test_supported_agent_get_swe_crafter() -> None:
    # Arrange
    open_ai_settings = OpenAISettings(
        api_key="s3cr3t-k3y",
    )
    # Act
    agent = SupportedAgent.get(
        SupportedAgent.SWE_CRAFTER,
        open_ai_settings,
    )

    # Assert
    assert isinstance(agent, SweCrafterOnDocker)
    assert agent.env_vars.get("OPENAI_API_KEY") == "s3cr3t-k3y"
