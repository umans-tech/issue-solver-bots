"""Tests for PostgresTokenUsageStorage."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock
import json

import pytest

from issue_solver.models.supported_models import QualifiedAIModel, SupportedAnthropicModel
from issue_solver.token_usage import TokenUsage
from issue_solver.token_usage.postgres_token_usage_storage import PostgresTokenUsageStorage


@pytest.mark.asyncio
async def test_store_token_usage():
    """Test storing a token usage record."""
    connection = AsyncMock()
    storage = PostgresTokenUsageStorage(connection)
    
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
    
    await storage.store(usage)
    
    connection.execute.assert_called_once()
    args = connection.execute.call_args[0]
    
    # Verify the SQL query
    assert "INSERT INTO process_token_usage" in args[0]
    
    # Verify the parameters
    assert args[1] == "test-process-123"  # process_id
    assert args[2] == "op_1"  # operation_id
    assert args[3] == "anthropic"  # provider
    assert args[4] == "claude-sonnet-4-20250514"  # model string representation
    assert args[5] == json.dumps({"input_tokens": 100, "output_tokens": 50})  # raw_usage_data
    assert args[6] == 0.0025  # total_cost_usd
    assert args[7] == datetime(2025, 1, 20, 15, 30, 0)  # occurred_at


@pytest.mark.asyncio
async def test_find_by_process_id():
    """Test retrieving token usage records by process ID."""
    connection = AsyncMock()
    storage = PostgresTokenUsageStorage(connection)
    
    # Mock database rows
    mock_rows = [
        {
            "process_id": "test-process-456",
            "operation_id": "op_1",
            "provider": "anthropic",
            "model": "claude-3-5-sonnet",
            "raw_usage_data": json.dumps({"tokens": 100}),
            "total_cost_usd": 0.001,
            "occurred_at": datetime(2025, 1, 20, 15, 30, 0),
        },
        {
            "process_id": "test-process-456",
            "operation_id": "op_2",
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "raw_usage_data": json.dumps({"input_tokens": 150, "output_tokens": 75}),
            "total_cost_usd": 0.002,
            "occurred_at": datetime(2025, 1, 20, 15, 35, 0),
        },
    ]
    
    connection.fetch.return_value = mock_rows
    
    result = await storage.find_by_process_id("test-process-456")
    
    # Verify the query
    connection.fetch.assert_called_once()
    args = connection.fetch.call_args[0]
    assert "SELECT" in args[0]
    assert "FROM process_token_usage" in args[0]
    assert "WHERE process_id = $1" in args[0]
    assert args[1] == "test-process-456"
    
    # Verify the results
    assert len(result) == 2
    
    # Check first record
    assert result[0].process_id == "test-process-456"
    assert result[0].operation_id == "op_1"
    assert result[0].provider == "anthropic"
    assert result[0].model.ai_model == SupportedAnthropicModel.CLAUDE_35_SONNET
    assert result[0].model.version is None
    assert result[0].raw_usage_data == {"tokens": 100}
    assert result[0].total_cost_usd == 0.001
    assert result[0].occurred_at == datetime(2025, 1, 20, 15, 30, 0)
    
    # Check second record
    assert result[1].process_id == "test-process-456"
    assert result[1].operation_id == "op_2"
    assert result[1].provider == "anthropic"
    assert result[1].model.ai_model == SupportedAnthropicModel.CLAUDE_SONNET_4
    assert result[1].model.version == "20250514"
    assert result[1].raw_usage_data == {"input_tokens": 150, "output_tokens": 75}
    assert result[1].total_cost_usd == 0.002
    assert result[1].occurred_at == datetime(2025, 1, 20, 15, 35, 0)


@pytest.mark.asyncio
async def test_find_by_process_id_empty_result():
    """Test retrieving token usage records when no records exist."""
    connection = AsyncMock()
    storage = PostgresTokenUsageStorage(connection)
    
    connection.fetch.return_value = []
    
    result = await storage.find_by_process_id("nonexistent-process")
    
    assert result == []
    
    connection.fetch.assert_called_once()
    args = connection.fetch.call_args[0]
    assert args[1] == "nonexistent-process"