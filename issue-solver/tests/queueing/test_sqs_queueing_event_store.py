import json
from datetime import datetime

import pytest

from issue_solver.events.domain import IssueResolutionCompleted
from tests.queueing.conftest import receive_event_message


@pytest.mark.asyncio
async def test_append_should_append_event_to_event_store_and_publish_to_sqs(
    event_store, sqs_queue, sqs_client
):
    # Given
    process_id = "test_process_id"
    event = IssueResolutionCompleted(
        process_id=process_id,
        occurred_at=datetime.fromisoformat("2023-10-01T00:00:00Z"),
        pr_number=123,
        pr_url="https://example.com/pr/123",
    )
    # When
    await event_store.append(process_id, event)
    # Then
    events = await event_store.get(process_id)
    assert events == [event]
    messages = receive_event_message(sqs_client, sqs_queue)
    assert "Messages" in messages
    message_body = json.loads(messages["Messages"][0]["Body"])
    assert message_body["process_id"] == process_id
    assert message_body["type"] == "issue_resolution_completed"
    assert message_body["pr_number"] == 123
    assert message_body["pr_url"] == "https://example.com/pr/123"
    assert message_body["occurred_at"] == "2023-10-01T00:00:00Z"
