from unittest.mock import Mock

import pytest
from claude_code_sdk import UserMessage

from issue_solver.agents.agent_message_store import (
    InMemoryAgentMessageStore,
    AgentMessage,
)
from issue_solver.agents.supported_agents import SupportedAgent
from issue_solver.cli.webhook_notifying_agent_message_store import (
    WebhookNotifyingAgentMessageStore,
)
from issue_solver.factories import init_agent_message_store
from issue_solver.models.supported_models import (
    VersionedAIModel,
    SupportedAnthropicModel,
    LATEST_CLAUDE_4_VERSION,
)
from issue_solver.streaming.streaming_agent_message_store import (
    StreamingAgentMessageStore,
)


@pytest.mark.asyncio
async def test_init_agent_message_store_should_return_inmemory_webhook_notifying_agent_message_store_when_messages_webhook_url_provided():
    # When
    agent_message_store = await init_agent_message_store(
        webhook_base_url="https://api.example.umans.ai",
    )

    # Then
    assert isinstance(agent_message_store, WebhookNotifyingAgentMessageStore)
    assert (
        agent_message_store.messages_webhook_url
        == "https://api.example.umans.ai/webhooks/messages"
    )


@pytest.mark.asyncio
async def test_init_agent_message_store_should_return_webhook_notifying_agent_message_store_when_messages_webhook_url_provided(
    database_url,
):
    # When
    agent_message_store = await init_agent_message_store(
        database_url=database_url,
        webhook_base_url="https://api.example.umans.ai",
    )

    # Then
    assert isinstance(agent_message_store, WebhookNotifyingAgentMessageStore)
    assert (
        agent_message_store.messages_webhook_url
        == "https://api.example.umans.ai/webhooks/messages"
    )


@pytest.mark.asyncio
async def test_init_agent_message_store_should_tolerate_trailing_slash_in_messages_webhook_url(
    database_url,
):
    # When
    agent_message_store = await init_agent_message_store(
        database_url=database_url,
        webhook_base_url="https://api.example.umans.ai/",
    )

    # Then
    assert isinstance(agent_message_store, WebhookNotifyingAgentMessageStore)
    assert (
        agent_message_store.messages_webhook_url
        == "https://api.example.umans.ai/webhooks/messages"
    )


@pytest.mark.asyncio
async def test_init_agent_message_store_should_return_streaming_agent_message_store_when_redis_url_provided(
    database_url,
):
    # When
    agent_message_store = await init_agent_message_store(
        database_url=database_url,
        redis_url="rediss://secure.instance:6379",
    )

    # Then
    assert isinstance(agent_message_store, StreamingAgentMessageStore)


@pytest.mark.asyncio
async def test_init_agent_message_store_should_return_inmemory_streaming_agent_message_store_when_redis_url_provided():
    # When
    agent_message_store = await init_agent_message_store(
        redis_url="rediss://secure.instance:6379",
    )

    # Then
    assert isinstance(agent_message_store, StreamingAgentMessageStore)


@pytest.mark.asyncio
async def test_init_agent_message_store_should_raise_exception_when_both_redis_url_and_event_webhook_url_provided(
    database_url,
):
    # When / Then
    with pytest.raises(ValueError):
        await init_agent_message_store(
            database_url=database_url,
            redis_url="rediss://secure.instance:6379",
            webhook_base_url="https://api.example.umans.ai",
        )


@pytest.mark.asyncio
async def test_webhook_notifying_agent_message_store_should_append_and_get_messages():
    # Given
    process_id = "test-process-id"
    message = UserMessage(
        content="Hello, can you solve this issue about serialization?"
    )
    http_client_mock = Mock()
    http_client_mock.post.return_value.status_code = 200

    # Mock dependencies
    agent_message_store = WebhookNotifyingAgentMessageStore(
        InMemoryAgentMessageStore(),
        messages_webhook_url="https://api.example.umans.ai/webhooks/messages",
        http_client=http_client_mock,
    )

    # When
    message_id = await agent_message_store.append(
        process_id=process_id,
        model=VersionedAIModel(
            ai_model=SupportedAnthropicModel.CLAUDE_OPUS_4,
            version=LATEST_CLAUDE_4_VERSION,
        ),
        message=message,
        turn=1,
        agent=SupportedAgent.CLAUDE_CODE,
    )

    # Then
    retrieved_messages = await agent_message_store.get(process_id)
    assert retrieved_messages == [
        AgentMessage(
            id=message_id,
            type="UserMessage",
            turn=1,
            agent=SupportedAgent.CLAUDE_CODE,
            model=VersionedAIModel(
                ai_model=SupportedAnthropicModel.CLAUDE_OPUS_4,
                version=LATEST_CLAUDE_4_VERSION,
            ),
            payload={"content": "Hello, can you solve this issue about serialization?"},
        )
    ]
    http_client_mock.post.assert_called_once_with(
        url="https://api.example.umans.ai/webhooks/messages",
        json={
            "process_id": process_id,
            "agent_message": {
                "id": message_id,
                "payload": {
                    "content": "Hello, can you solve this issue about serialization?"
                },
                "model": {"ai_model": "claude-opus-4", "version": "20250514"},
                "turn": 1,
                "agent": "claude-code",
                "type": "UserMessage",
            },
        },
    )
