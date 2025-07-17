"""Tests for TokenUsage value object."""

from datetime import datetime

import pytest

from issue_solver.models.supported_models import QualifiedAIModel, SupportedAnthropicModel
from issue_solver.token_usage import TokenUsage


def test_token_usage_creation():
    """Test creating a TokenUsage object with all required fields."""
    model = QualifiedAIModel(
        ai_model=SupportedAnthropicModel.CLAUDE_SONNET_4,
        version="20250514"
    )
    
    usage = TokenUsage(
        process_id="test-process-123",
        operation_id="op_1",
        provider="anthropic",
        model=model,
        raw_usage_data={"input_tokens": 100, "output_tokens": 50},
        total_cost_usd=0.0025,
        occurred_at=datetime(2025, 1, 20, 15, 30, 0),
    )
    
    assert usage.process_id == "test-process-123"
    assert usage.operation_id == "op_1"
    assert usage.provider == "anthropic"
    assert usage.model == model
    assert usage.raw_usage_data == {"input_tokens": 100, "output_tokens": 50}
    assert usage.total_cost_usd == 0.0025
    assert usage.occurred_at == datetime(2025, 1, 20, 15, 30, 0)


def test_token_usage_optional_cost():
    """Test creating a TokenUsage object without cost information."""
    model = QualifiedAIModel(
        ai_model=SupportedAnthropicModel.CLAUDE_35_SONNET,
    )
    
    usage = TokenUsage(
        process_id="test-process-456",
        operation_id="op_2",
        provider="anthropic",
        model=model,
        raw_usage_data={"tokens": 150},
        occurred_at=datetime(2025, 1, 20, 16, 0, 0),
    )
    
    assert usage.total_cost_usd is None


def test_token_usage_immutable():
    """Test that TokenUsage is immutable (frozen dataclass)."""
    model = QualifiedAIModel(
        ai_model=SupportedAnthropicModel.CLAUDE_35_HAIKU,
    )
    
    usage = TokenUsage(
        process_id="test-process-789",
        operation_id="op_3",
        provider="anthropic",
        model=model,
        raw_usage_data={"usage": "test"},
        occurred_at=datetime(2025, 1, 20, 17, 0, 0),
    )
    
    # Should not be able to modify fields
    with pytest.raises(AttributeError):
        usage.process_id = "modified"
    
    with pytest.raises(AttributeError):
        usage.total_cost_usd = 0.01