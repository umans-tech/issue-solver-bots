from unittest.mock import ANY

import pytest
from claude_code_sdk import SystemMessage

from issue_solver.agents.agent_message_store import AgentMessageStore
from issue_solver.models.supported_models import (
    VersionedAIModel,
    SupportedAnthropicModel,
)


@pytest.mark.asyncio
async def test_get_process_messages_streaming_with_one_historical_message(
    agent_message_store: AgentMessageStore, api_client
):
    # Given
    original_message_data = await first_system_message()
    original_message = {
        "data": original_message_data,
        "subtype": "init",
    }
    process_id = "process-1"
    await agent_message_store.append(
        process_id=process_id,
        model=VersionedAIModel(
            SupportedAnthropicModel.CLAUDE_SONNET_4, version="20250514"
        ),
        turn=1,
        message=SystemMessage(data=original_message_data, subtype="init"),
    )

    # When
    response = api_client.get(f"/processes/{process_id}/messages")

    # Then
    assert response.status_code == 200, response.text

    messages_data = response.json()
    message = {
        "id": ANY,
        "type": "SystemMessage",
        "turn": 1,
        "agent": "CLAUDE_CODE",
        "model": "claude-sonnet-4-20250514",
        "payload": original_message,
    }
    assert message == messages_data, (
        f"Expected message {message} not found in {messages_data}"
    )


async def first_system_message():
    return {
        "cwd": "/tmp/repo/bed8374f-535e-4e50-a7d9-49346eb8263c",
        "type": "system",
        "model": "claude-sonnet-4-20250514",
        "tools": [
            "Task",
            "Bash",
            "Glob",
            "Grep",
            "LS",
            "exit_plan_mode",
            "Read",
            "Edit",
            "MultiEdit",
            "Write",
            "NotebookRead",
            "NotebookEdit",
            "WebFetch",
            "TodoWrite",
            "WebSearch",
        ],
        "subtype": "init",
        "session_id": "anthropic-session-1",
        "mcp_servers": [],
        "apiKeySource": "ANTHROPIC_API_KEY",
        "permissionMode": "bypassPermissions",
    }
