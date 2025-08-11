import pytest
from pydantic import AnyUrl

from issue_solver.agents.anthropic_agent import AnthropicAgent
from issue_solver.agents.claude_code_agent import ClaudeCodeAgent
from issue_solver.agents.openai_agent import OpenAIAgent
from issue_solver.agents.supported_agents import SupportedAgent
from issue_solver.agents.swe_agents_on_docker import (
    SweAgentOnDocker,
    SweCrafterOnDocker,
)
from issue_solver.models.model_settings import OpenAISettings, AnthropicSettings


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


def test_supported_agent_get_anthropic_tools() -> None:
    # Arrange
    anthropic_settings = AnthropicSettings(
        api_key="s3cr3t-k3y",
        base_url=AnyUrl("https://api.anthropic.com/v1"),
    )

    # Act
    agent = SupportedAgent.get(
        SupportedAgent.ANTHROPIC_TOOLS,
        anthropic_settings,
    )
    # Assert
    assert isinstance(agent, AnthropicAgent)
    assert agent.api_key == "s3cr3t-k3y"


def test_supported_agent_get_openai_tools() -> None:
    # Arrange
    open_ai_settings = OpenAISettings(
        api_key="s3cr3t-k3y",
        base_url=AnyUrl("https://api.openai.com/v1"),
    )
    # Act
    agent = SupportedAgent.get(
        SupportedAgent.OPENAI_TOOLS,
        open_ai_settings,
    )
    # Assert
    assert isinstance(
        agent, OpenAIAgent
    )  # Placeholder, as OPENAI_TOOLS is not implemented yet
    assert agent.client.api_key == "s3cr3t-k3y"


def test_supported_agent_get_claude_code() -> None:
    # Arrange
    anthropic_settings = AnthropicSettings(
        api_key="s3cr3t-k3y",
        base_url=AnyUrl("https://api.anthropic.com/v1"),
    )

    # Act
    agent = SupportedAgent.get(
        SupportedAgent.CLAUDE_CODE,
        anthropic_settings,
    )
    # Assert
    assert isinstance(agent, ClaudeCodeAgent)
    assert agent.api_key == "s3cr3t-k3y"


def test_supported_agent_get_should_raise_an_error_when_claude_code_agent_with_openai_settings() -> (
    None
):
    # Arrange
    open_ai_settings = OpenAISettings(
        api_key="s3cr3t-k3y",
        base_url=AnyUrl("https://api.openai.com/v1"),
    )
    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        SupportedAgent.get(
            SupportedAgent.CLAUDE_CODE,
            open_ai_settings,
        )
    assert str(exc_info.value) == (
        "Claude Code Agent requires AnthropicSettings for model settings, but OpenAISettings were provided."
    )
