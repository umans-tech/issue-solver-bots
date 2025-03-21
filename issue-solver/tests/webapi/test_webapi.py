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


def test_get_process_returns_404_when_process_is_not_found(api_client):
    # When
    response = api_client.get("/processes/123")

    # Then
    assert response.status_code == 404


def test_get_process_returns_200_when_the_process_is_found(
    api_client, time_under_control
):
    # Given
    time_under_control.set_from_iso_format("2021-01-01T00:00:00")
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/test/repo",
            "access_token": "test-access-token",
        },
    )
    process_id = connect_repo_response.json()["process_id"]

    # When
    response = api_client.get(f"/processes/{process_id}")

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "id": process_id,
        "type": "code_repository_integration",
        "status": "connected",
        "events": [
            {
                "type": "repository_connected",
                "occurred_at": "2021-01-01T00:00:00",
                "url": "https://github.com/test/repo",
                "access_token": "***********oken",
                "user_id": "Todo: get user id",
                "space_id": "Todo: get space id",
                "knowledge_base_id": CREATED_VECTOR_STORE_ID,
                "process_id": process_id,
            }
        ],
    }
