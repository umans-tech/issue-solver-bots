import json

import pytest

from issue_solver.events.serializable_records import serialize, deserialize
from tests.examples.happy_path_persona import examples_of_all_events
from tests.webapi.test_webapi import receive_event_message


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
