import json

import pytest
from redis.client import PubSub
from tests.examples.happy_path_persona import examples_of_all_events
from tests.webapi.conftest import receive_event_message

from issue_solver.events.serializable_records import serialize, deserialize


@pytest.mark.parametrize(
    "event_type,event",
    examples_of_all_events(),
)
def test_webhook_event_handling(event_type, event, api_client, sqs_client, sqs_queue):
    # When
    response = api_client.post(
        "/webhooks/events", json=serialize(event).model_dump(mode="json")
    )

    # Then
    assert response.status_code == 200
    messages = receive_event_message(sqs_client, sqs_queue)
    assert "Messages" in messages
    body_of_first_received_message = messages["Messages"][0]["Body"]
    message_type = json.loads(body_of_first_received_message)["type"]
    published_event = deserialize(message_type, body_of_first_received_message)
    assert published_event == event


@pytest.mark.asyncio
def test_agent_messages_webhook_should_publish_message_to_redis_channel(
    redis_client, api_client
):
    # Given
    process_id = "test-process-id"
    agent_message_payload = {"role": "user", "content": "Hello, how can I help you?"}
    subscriber = redis_client.pubsub()
    subscriber.subscribe("process:test-process-id:messages")

    # When
    response = api_client.post(
        "/webhooks/messages",
        json={
            "process_id": process_id,
            "agentMessage": {
                "id": "message-id-123",
                "payload": agent_message_payload,
                "model": {"ai_model": "claude-opus-4", "version": "20250514"},
                "turn": 1,
                "agent": "claude-code",
                "type": "SystemMessage",
            },
        },
    )
    # Then
    assert response.status_code == 200
    first_published_message = get_first_published_message(subscriber)

    assert first_published_message is not None
    assert first_published_message["type"] == "message"
    data = json.loads(first_published_message["data"])
    assert data["id"] == "message-id-123"
    assert data["payload"] == agent_message_payload


def get_first_published_message(subscriber: PubSub) -> dict | None:
    published_message = subscriber.get_message(timeout=1)
    while published_message:
        if published_message["type"] != "subscribe":
            return published_message
        published_message = subscriber.get_message(timeout=1)
    return published_message
