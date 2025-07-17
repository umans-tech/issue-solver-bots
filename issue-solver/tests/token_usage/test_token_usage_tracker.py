"""Tests for TokenUsageTracker service."""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from issue_solver.models.supported_models import QualifiedAIModel, SupportedAnthropicModel
from issue_solver.token_usage import TokenUsage, TokenUsageTracker


@pytest.mark.asyncio
async def test_record_usage():
    """Test that the tracker records usage through storage."""
    storage = AsyncMock()
    tracker = TokenUsageTracker(storage)
    
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
    
    await tracker.record_usage(usage)
    
    storage.store.assert_called_once_with(usage)


@pytest.mark.asyncio
async def test_get_usage_for_process():
    """Test that the tracker retrieves usage for a process through storage."""
    storage = AsyncMock()
    tracker = TokenUsageTracker(storage)
    
    process_id = "test-process-456"
    expected_usage_records = [
        TokenUsage(
            process_id=process_id,
            operation_id="op_1",
            provider="anthropic",
            model=QualifiedAIModel(ai_model=SupportedAnthropicModel.CLAUDE_35_SONNET),
            raw_usage_data={"tokens": 100},
            occurred_at=datetime(2025, 1, 20, 15, 30, 0),
        ),
        TokenUsage(
            process_id=process_id,
            operation_id="op_2",
            provider="anthropic",
            model=QualifiedAIModel(ai_model=SupportedAnthropicModel.CLAUDE_35_SONNET),
            raw_usage_data={"tokens": 150},
            occurred_at=datetime(2025, 1, 20, 15, 35, 0),
        ),
    ]
    
    storage.find_by_process_id.return_value = expected_usage_records
    
    result = await tracker.get_usage_for_process(process_id)
    
    storage.find_by_process_id.assert_called_once_with(process_id)
    assert result == expected_usage_records