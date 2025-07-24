import json
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
        agent="CLAUDE_CODE",
    )

    # When
    response = api_client.get(f"/processes/{process_id}/messages/stream")

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
    assert messages_data == message, (
        f"Expected message {message} not found in {messages_data}"
    )


@pytest.mark.asyncio
async def test_get_process_messages_streaming_with_two_historical_messages(
    agent_message_store: AgentMessageStore, api_client
):
    # Given
    original_message_data = await first_system_message()
    original_message = {
        "data": original_message_data,
        "subtype": "init \n",
    }
    process_id = "process-2"
    await agent_message_store.append(
        process_id=process_id,
        model=VersionedAIModel(
            SupportedAnthropicModel.CLAUDE_SONNET_4, version="20250514"
        ),
        turn=1,
        message=SystemMessage(data=original_message_data, subtype="init \n"),
        agent="CLAUDE_CODE",
    )

    second_message_data = {
        "data": {"text": "This is a follow-up message."},
        "subtype": "follow_up",
    }
    second_message = {
        "data": second_message_data,
        "subtype": "follow_up",
    }
    await agent_message_store.append(
        process_id=process_id,
        model=VersionedAIModel(
            SupportedAnthropicModel.CLAUDE_SONNET_4, version="20250514"
        ),
        turn=2,
        message=SystemMessage(data=second_message_data, subtype="follow_up"),
        agent="CLAUDE_CODE",
    )

    # When
    received_messages = []
    with api_client.stream(
        "GET", f"/processes/{process_id}/messages/stream"
    ) as response:
        status_code = response.status_code
        for chunk in response.iter_lines():
            if chunk:
                received_messages.append(json.loads(chunk))

    # Then
    assert status_code == 200

    first_message = {
        "id": ANY,
        "type": "SystemMessage",
        "turn": 1,
        "agent": "CLAUDE_CODE",
        "model": "claude-sonnet-4-20250514",
        "payload": original_message,
    }
    second_message_expected = {
        "id": ANY,
        "type": "SystemMessage",
        "turn": 2,
        "agent": "CLAUDE_CODE",
        "model": "claude-sonnet-4-20250514",
        "payload": second_message,
    }

    assert first_message in received_messages, (
        f"Expected first message {first_message} not found in {received_messages}"
    )
    assert second_message_expected in received_messages, (
        f"Expected second message {second_message_expected} not found in {received_messages}"
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
