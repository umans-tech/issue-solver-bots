import json

import pytest
from claude_code_sdk import AssistantMessage, TextBlock
from redis.client import PubSub

from issue_solver.agents.agent_message_store import (
    InMemoryAgentMessageStore,
    AgentMessage,
)
from issue_solver.agents.supported_agents import SupportedAgent
from issue_solver.models.supported_models import (
    VersionedAIModel,
    SupportedAnthropicModel,
    LATEST_CLAUDE_4_VERSION,
)
from issue_solver.streaming.streaming_agent_message_store import (
    StreamingAgentMessageStore,
)


@pytest.mark.asyncio
async def test_streaming_agent_message_store_should_append_and_publish(redis_client):
    # Given
    agent_message_store = InMemoryAgentMessageStore()
    streaming_agent_message_store = StreamingAgentMessageStore(
        message_store=agent_message_store, redis_client=redis_client
    )
    subscriber = redis_client.pubsub()
    subscriber.subscribe("process:resolve-issue-123:messages")

    # When
    message_id = await streaming_agent_message_store.append(
        process_id="resolve-issue-123",
        model=VersionedAIModel(
            ai_model=SupportedAnthropicModel.CLAUDE_SONNET_4,
            version=LATEST_CLAUDE_4_VERSION,
        ),
        turn=5,
        agent=SupportedAgent.CLAUDE_CODE,
        message=AssistantMessage(
            content=[TextBlock(text="I understand the issue now. Let's fix it.")],
        ),
    )

    # Then
    process_messages = await agent_message_store.get(process_id="resolve-issue-123")
    payload = {"content": [{"text": "I understand the issue now. Let's fix it."}]}
    expected_agent_message = AgentMessage(
        id=message_id,
        type="AssistantMessage",
        turn=5,
        agent=SupportedAgent.CLAUDE_CODE,
        model=VersionedAIModel(ai_model="claude-sonnet-4", version="20250514"),
        payload=payload,
    )
    assert process_messages == [expected_agent_message]

    first_published_message = get_first_published_message(subscriber)
    assert first_published_message is not None
    assert first_published_message["type"] == "message"
    data = json.loads(first_published_message["data"])
    assert data["id"] == message_id
    assert data["payload"] == payload
    assert data["turn"] == 5
    assert data["agent"] == SupportedAgent.CLAUDE_CODE
    assert data["model"] == {"ai_model": "claude-sonnet-4", "version": "20250514"}


def get_first_published_message(subscriber: PubSub) -> dict | None:
    published_message = subscriber.get_message(timeout=1)
    while published_message:
        if published_message["type"] != "subscribe":
            return published_message
        published_message = subscriber.get_message(timeout=1)
    return published_message
