"""Integration tests for ClaudeCodeAgent with token tracking."""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
import pytest

from issue_solver.agents.claude_code_agent import ClaudeCodeAgent
from issue_solver.agents.issue_resolving_agent import ResolveIssueCommand
from issue_solver.issues.issue import IssueInfo
from issue_solver.models.supported_models import QualifiedAIModel, SupportedAnthropicModel
from issue_solver.token_usage import TokenUsage, TokenUsageTracker


@pytest.mark.asyncio
async def test_claude_code_agent_without_tracker():
    """Test that ClaudeCodeAgent works without a token usage tracker."""
    agent = ClaudeCodeAgent(api_key="test-api-key")
    
    # Should work fine without a tracker
    assert agent.token_usage_tracker is None


@pytest.mark.asyncio
async def test_claude_code_agent_with_tracker_records_usage():
    """Test that ClaudeCodeAgent records usage when tracker is provided."""
    tracker = AsyncMock(spec=TokenUsageTracker)
    agent = ClaudeCodeAgent(api_key="test-api-key", token_usage_tracker=tracker)
    
    command = ResolveIssueCommand(
        model=QualifiedAIModel(
            ai_model=SupportedAnthropicModel.CLAUDE_SONNET_4,
            version="20250514"
        ),
        issue=IssueInfo(title="Test Issue", description="Test description"),
        repo_path=Path("/tmp/test-repo"),
        process_id="test-process-123",
    )
    
    # Mock the claude_code_sdk.query function
    mock_result_message = Mock()
    mock_result_message.total_cost_usd = 0.0125
    mock_result_message.__class__.__name__ = "ResultMessage"
    
    async def mock_query(*args, **kwargs):
        yield mock_result_message
    
    with patch("issue_solver.agents.claude_code_agent.query", side_effect=mock_query):
        await agent.resolve_issue(command)
    
    # Verify that usage was recorded
    tracker.record_usage.assert_called_once()
    
    # Verify the usage record content
    recorded_usage = tracker.record_usage.call_args[0][0]
    assert isinstance(recorded_usage, TokenUsage)
    assert recorded_usage.process_id == "test-process-123"
    assert recorded_usage.operation_id == "op_0"
    assert recorded_usage.provider == "anthropic"
    assert recorded_usage.model == command.model
    assert recorded_usage.total_cost_usd == 0.0125
    assert "total_cost_usd" in recorded_usage.raw_usage_data
    assert recorded_usage.raw_usage_data["total_cost_usd"] == 0.0125
    assert recorded_usage.raw_usage_data["message_type"] == "ResultMessage"


@pytest.mark.asyncio
async def test_claude_code_agent_ignores_zero_cost_messages():
    """Test that ClaudeCodeAgent ignores messages with zero or None cost."""
    tracker = AsyncMock(spec=TokenUsageTracker)
    agent = ClaudeCodeAgent(api_key="test-api-key", token_usage_tracker=tracker)
    
    command = ResolveIssueCommand(
        model=QualifiedAIModel(
            ai_model=SupportedAnthropicModel.CLAUDE_35_SONNET,
        ),
        issue=IssueInfo(title="Test Issue", description="Test description"),
        repo_path=Path("/tmp/test-repo"),
        process_id="test-process-456",
    )
    
    # Mock the claude_code_sdk.query function with zero cost
    mock_result_message = Mock()
    mock_result_message.total_cost_usd = 0.0
    mock_result_message.__class__.__name__ = "ResultMessage"
    
    async def mock_query(*args, **kwargs):
        yield mock_result_message
    
    with patch("issue_solver.agents.claude_code_agent.query", side_effect=mock_query):
        await agent.resolve_issue(command)
    
    # Should not record usage for zero cost
    tracker.record_usage.assert_not_called()


@pytest.mark.asyncio
async def test_claude_code_agent_ignores_none_cost_messages():
    """Test that ClaudeCodeAgent ignores messages with None cost."""
    tracker = AsyncMock(spec=TokenUsageTracker)
    agent = ClaudeCodeAgent(api_key="test-api-key", token_usage_tracker=tracker)
    
    command = ResolveIssueCommand(
        model=QualifiedAIModel(
            ai_model=SupportedAnthropicModel.CLAUDE_35_HAIKU,
        ),
        issue=IssueInfo(title="Test Issue", description="Test description"),
        repo_path=Path("/tmp/test-repo"),
        process_id="test-process-789",
    )
    
    # Mock the claude_code_sdk.query function with None cost
    mock_result_message = Mock()
    mock_result_message.total_cost_usd = None
    mock_result_message.__class__.__name__ = "ResultMessage"
    
    async def mock_query(*args, **kwargs):
        yield mock_result_message
    
    with patch("issue_solver.agents.claude_code_agent.query", side_effect=mock_query):
        await agent.resolve_issue(command)
    
    # Should not record usage for None cost
    tracker.record_usage.assert_not_called()