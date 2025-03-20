import json

from tests.webapi.conftest import CREATED_VECTOR_STORE_ID


def test_connect_repository_returns_201_and_publishes_code_repository_connected_event(
    api_client, sqs_client, sqs_queue
):
    # Given
    repo_url = "https://github.com/test/repo"
    repo_access_token = "test-access-token"

    # When
    response = api_client.post(
        "/repositories/", json={"url": repo_url, "access_token": repo_access_token}
    )

    # Then
    assert response.status_code == 201
    data = response.json()
    assert data["url"] == repo_url
    assert "process_id" in data
    assert data["knowledge_base_id"] == CREATED_VECTOR_STORE_ID
    # Verify message was sent to SQS
    queue_url = sqs_queue["queue_url"]
    messages = sqs_client.receive_message(
        QueueUrl=queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=1
    )
    assert "Messages" in messages
    message_body = json.loads(messages["Messages"][0]["Body"])
    assert message_body["url"] == repo_url
    assert message_body["access_token"] == repo_access_token
    assert message_body["process_id"] == data["process_id"]
    assert message_body["knowledge_base_id"] == CREATED_VECTOR_STORE_ID
