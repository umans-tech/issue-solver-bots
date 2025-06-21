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
        "/repositories/",
        json={
            "url": repo_url,
            "access_token": repo_access_token,
            "space_id": "test-space-id",
        },
        headers={
            "X-User-ID": "test-user-id",
        },
    )

    # Then
    assert response.status_code == 201
    data = response.json()
    assert data["url"] == repo_url
    assert "process_id" in data
    assert data["knowledge_base_id"] == CREATED_VECTOR_STORE_ID
    # Verify message was sent to SQS
    messages = receive_event_message(sqs_client, sqs_queue)
    assert "Messages" in messages
    message_body = json.loads(messages["Messages"][0]["Body"])
    assert message_body["url"] == repo_url
    assert message_body["access_token"] == repo_access_token
    assert message_body["process_id"] == data["process_id"]
    assert message_body["knowledge_base_id"] == CREATED_VECTOR_STORE_ID
    assert message_body["user_id"] == "test-user-id"
    assert message_body["space_id"] == "test-space-id"


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
            "space_id": "test-space-id",
        },
        headers={
            "X-User-ID": "test-user-id",
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
                "access_token": "*************oken",
                "user_id": "test-user-id",
                "space_id": "test-space-id",
                "knowledge_base_id": CREATED_VECTOR_STORE_ID,
                "process_id": process_id,
            }
        ],
    }


def test_post_repositories_index_new_changes(
    api_client, time_under_control, sqs_client, sqs_queue
):
    # Given
    time_under_control.set_from_iso_format("2021-01-01T00:00:00")
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/test/repo",
            "access_token": "test-access-token",
            "space_id": "test-space-id",
        },
        headers={
            "X-User-ID": "test-user-id",
        },
    )
    connect_repo_response_json = connect_repo_response.json()
    process_id = connect_repo_response_json["process_id"]
    knowledge_base_id = connect_repo_response_json["knowledge_base_id"]
    receive_event_message(sqs_client, sqs_queue)

    # When
    response = api_client.post(
        f"/repositories/{knowledge_base_id}",
        headers={
            "X-User-ID": "second-user-id",
        },
    )

    # Then
    assert response.status_code == 200
    # Verify message was sent to SQS
    messages = receive_event_message(sqs_client, sqs_queue)
    assert "Messages" in messages
    message_body = json.loads(messages["Messages"][0]["Body"])
    assert message_body["type"] == "repository_indexation_requested"
    assert message_body["process_id"] == process_id
    assert message_body["user_id"] == "second-user-id"
    assert message_body["occurred_at"] == "2021-01-01T00:00:00"


def test_connect_repository_should_raise_401_when_authentication_fails(
    api_client, repo_validation_under_control
):
    # Given
    repo_validation_under_control.add_inaccessible_repository(
        url="https://github.com/test/repo",
        error_type="authentication_failed",
        status_code=401,
    )

    # When
    response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/test/repo",
            "access_token": "test-access-token",
            "user_id": "test-user-id",
            "space_id": "test-space-id",
        },
    )

    # Then
    assert response.status_code == 401


def receive_event_message(sqs_client, sqs_queue):
    return sqs_client.receive_message(
        QueueUrl=sqs_queue["queue_url"], MaxNumberOfMessages=1, WaitTimeSeconds=1
    )
