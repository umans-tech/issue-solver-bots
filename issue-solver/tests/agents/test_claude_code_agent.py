import pytest
from unittest.mock import patch, AsyncMock
from pathlib import Path

from issue_solver.agents.claude_code_agent import ClaudeCodeAgent, ClaudeCodeTurnOutput
from issue_solver.agents.issue_resolving_agent import ResolveIssueCommand
from issue_solver.issues.issue import IssueInfo
from issue_solver.models.supported_models import (
    SupportedAnthropicModel,
    QualifiedAIModel,
)


class TestClaudeCodeAgent:
    def test_init_with_api_key(self):
        """Test initialization with API key."""
        agent = ClaudeCodeAgent(api_key="test-key")
        assert agent.api_key == "test-key"
        assert agent.max_turns == 100
        assert agent.permission_mode == "acceptEdits"

    def test_init_without_api_key_raises_error(self):
        """Test that initialization without API key raises ValueError."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY environment variable is required"):
                ClaudeCodeAgent()

    def test_init_with_env_var(self):
        """Test initialization with environment variable."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-key"}):
            agent = ClaudeCodeAgent()
            assert agent.api_key == "env-key"

    def test_build_issue_prompt_with_title(self):
        """Test prompt building with issue title."""
        agent = ClaudeCodeAgent(api_key="test-key")
        command = ResolveIssueCommand(
            model=QualifiedAIModel(ai_model=SupportedAnthropicModel.CLAUDE_35_HAIKU),
            issue=IssueInfo(title="Test Issue", description="Test description"),
            repo_path=Path("/test/repo"),
        )
        
        prompt = agent._build_issue_prompt(command)
        
        assert "Test Issue" in prompt
        assert "Test description" in prompt
        assert "/test/repo" in prompt
        assert "Instructions:" in prompt

    def test_build_issue_prompt_without_title(self):
        """Test prompt building without issue title."""
        agent = ClaudeCodeAgent(api_key="test-key")
        command = ResolveIssueCommand(
            model=QualifiedAIModel(ai_model=SupportedAnthropicModel.CLAUDE_35_HAIKU),
            issue=IssueInfo(description="Test description only"),
            repo_path=Path("/test/repo"),
        )
        
        prompt = agent._build_issue_prompt(command)
        
        assert "Test description only" in prompt
        assert "/test/repo" in prompt
        assert "Issue Title:" not in prompt

    @pytest.mark.asyncio
    async def test_resolve_issue_success(self):
        """Test successful issue resolution."""
        agent = ClaudeCodeAgent(api_key="test-key")
        command = ResolveIssueCommand(
            model=QualifiedAIModel(ai_model=SupportedAnthropicModel.CLAUDE_35_HAIKU),
            issue=IssueInfo(description="Test issue"),
            repo_path=Path("/test/repo"),
        )

        # Mock successful Claude Code response
        mock_messages = [
            {"type": "init", "session_id": "test-session"},
            {"type": "assistant", "message": "I'll help you resolve this issue"},
            {"type": "result", "is_error": False, "duration_ms": 1000, "num_turns": 5, "total_cost_usd": 0.01}
        ]

        with patch("issue_solver.agents.claude_code_agent.query") as mock_query:
            mock_query.return_value.__aiter__ = AsyncMock(return_value=iter(mock_messages))
            
            # Should not raise any exception
            await agent.resolve_issue(command)

    @pytest.mark.asyncio
    async def test_resolve_issue_claude_code_error(self):
        """Test issue resolution when Claude Code returns error."""
        agent = ClaudeCodeAgent(api_key="test-key")
        command = ResolveIssueCommand(
            model=QualifiedAIModel(ai_model=SupportedAnthropicModel.CLAUDE_35_HAIKU),
            issue=IssueInfo(description="Test issue"),
            repo_path=Path("/test/repo"),
        )

        # Mock error response from Claude Code
        mock_messages = [
            {"type": "result", "is_error": True, "result": "Claude Code failed to execute"}
        ]

        with patch("issue_solver.agents.claude_code_agent.query") as mock_query:
            mock_query.return_value.__aiter__ = AsyncMock(return_value=iter(mock_messages))
            
            with pytest.raises(Exception, match="Claude Code execution failed"):
                await agent.resolve_issue(command)

    @pytest.mark.asyncio
    async def test_resolve_issue_no_messages(self):
        """Test issue resolution when Claude Code returns no messages."""
        agent = ClaudeCodeAgent(api_key="test-key")
        command = ResolveIssueCommand(
            model=QualifiedAIModel(ai_model=SupportedAnthropicModel.CLAUDE_35_HAIKU),
            issue=IssueInfo(description="Test issue"),
            repo_path=Path("/test/repo"),
        )

        with patch("issue_solver.agents.claude_code_agent.query") as mock_query:
            mock_query.return_value.__aiter__ = AsyncMock(return_value=iter([]))
            
            with pytest.raises(Exception, match="Claude Code produced no output"):
                await agent.resolve_issue(command)

    @pytest.mark.asyncio 
    async def test_resolve_issue_exception_handling(self):
        """Test issue resolution when Claude Code query raises exception."""
        agent = ClaudeCodeAgent(api_key="test-key")
        command = ResolveIssueCommand(
            model=QualifiedAIModel(ai_model=SupportedAnthropicModel.CLAUDE_35_HAIKU),
            issue=IssueInfo(description="Test issue"),
            repo_path=Path("/test/repo"),
        )

        with patch("issue_solver.agents.claude_code_agent.query") as mock_query:
            mock_query.side_effect = Exception("Claude Code SDK error")
            
            with pytest.raises(Exception, match="Claude Code agent execution failed"):
                await agent.resolve_issue(command)


class TestClaudeCodeTurnOutput:
    def test_has_finished_with_error(self):
        """Test has_finished returns True when there's an error."""
        output = ClaudeCodeTurnOutput([], has_error=True, error_message="Test error")
        assert output.has_finished() is True

    def test_has_finished_no_messages(self):
        """Test has_finished returns False when there are no messages."""
        output = ClaudeCodeTurnOutput([])
        assert output.has_finished() is False

    def test_has_finished_success_result(self):
        """Test has_finished returns True for successful result message."""
        messages = [{"type": "result", "is_error": False}]
        output = ClaudeCodeTurnOutput(messages)
        assert output.has_finished() is True

    def test_has_finished_error_result(self):
        """Test has_finished returns False for error result message."""
        messages = [{"type": "result", "is_error": True}]
        output = ClaudeCodeTurnOutput(messages)
        assert output.has_finished() is False

    def test_messages_history(self):
        """Test messages history conversion."""
        messages = [
            {"type": "assistant", "message": "Hello"},
            {"type": "user", "message": "Hi there"},
        ]
        output = ClaudeCodeTurnOutput(messages)
        history = output.messages_history()
        
        assert len(history) == 2
        assert history[0].role == "assistant"
        assert history[0].content == "Hello"
        assert history[1].role == "user"
        assert history[1].content == "Hi there" 