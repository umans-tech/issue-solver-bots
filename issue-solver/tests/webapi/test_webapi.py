import json

from tests.webapi.conftest import CREATED_VECTOR_STORE_ID, receive_event_message


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
                "token_permissions": None,
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


def test_connect_github_repository_includes_token_permissions(
    api_client, time_under_control, repo_validation_under_control
):
    # Given - Mock successful GitHub token validation with permissions
    time_under_control.set_from_iso_format("2021-01-01T00:00:00")
    repo_validation_under_control.mock_github_token_scopes(
        url="https://github.com/test/repo",
        access_token="github-token-with-scopes",
        scopes=["repo", "workflow", "read:user"],
    )

    # When
    response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/test/repo",
            "access_token": "github-token-with-scopes",
            "space_id": "test-space-id",
        },
        headers={
            "X-User-ID": "test-user-id",
        },
    )

    # Then
    assert response.status_code == 201
    process_id = response.json()["process_id"]

    # Check that token permissions are stored in the event
    process_response = api_client.get(f"/processes/{process_id}")
    assert process_response.status_code == 200
    process_data = process_response.json()

    repo_event = process_data["events"][0]
    assert repo_event["type"] == "repository_connected"
    assert repo_event["token_permissions"] is not None

    token_permissions = repo_event["token_permissions"]
    assert token_permissions["scopes"] == ["repo", "workflow", "read:user"]
    assert token_permissions["has_repo"] is True
    assert token_permissions["has_workflow"] is True
    assert token_permissions["has_read_user"] is True
    assert token_permissions["missing_scopes"] == []
    assert token_permissions["is_optimal"] is True


def test_rotate_token_returns_200_and_creates_token_rotated_event(
    api_client, time_under_control
):
    # Given - Create a repository first
    time_under_control.set_from_iso_format("2021-01-01T00:00:00")
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/test/repo",
            "access_token": "old-access-token",
            "space_id": "test-space-id",
        },
        headers={
            "X-User-ID": "test-user-id",
        },
    )
    knowledge_base_id = connect_repo_response.json()["knowledge_base_id"]
    process_id = connect_repo_response.json()["process_id"]

    # Move time forward for the token rotation
    time_under_control.set_from_iso_format("2021-01-01T01:00:00")

    # When - Rotate the token
    response = api_client.put(
        f"/repositories/{knowledge_base_id}/token",
        json={
            "access_token": "new-access-token",
        },
        headers={
            "X-User-ID": "test-user-id",
        },
    )

    # Then
    assert response.status_code == 200
    result = response.json()
    assert result["message"] == "Token rotated successfully"
    assert "token_permissions" in result

    # Verify the event was created by checking the process timeline
    process_response = api_client.get(f"/processes/{process_id}")
    assert process_response.status_code == 200
    process_data = process_response.json()

    # Should have 2 events: repository_connected and repository_token_rotated
    assert len(process_data["events"]) == 2

    # Check the token rotation event
    token_rotation_event = process_data["events"][1]
    assert token_rotation_event["type"] == "repository_token_rotated"
    assert token_rotation_event["occurred_at"] == "2021-01-01T01:00:00"
    assert token_rotation_event["knowledge_base_id"] == knowledge_base_id
    assert token_rotation_event["new_access_token"] == "************oken"  # Obfuscated
    assert token_rotation_event["user_id"] == "test-user-id"
    assert token_rotation_event["process_id"] == process_id


def test_rotate_token_returns_404_when_repository_not_found(api_client):
    # When
    response = api_client.put(
        "/repositories/nonexistent-kb/token",
        json={
            "access_token": "new-access-token",
        },
        headers={
            "X-User-ID": "test-user-id",
        },
    )

    # Then
    assert response.status_code == 404
    assert "No repository found" in response.json()["detail"]


def test_rotate_token_returns_401_when_new_token_is_invalid(
    api_client, time_under_control, repo_validation_under_control
):
    # Given - Create a repository first
    time_under_control.set_from_iso_format("2021-01-01T00:00:00")
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/test/repo",
            "access_token": "old-access-token",
            "space_id": "test-space-id",
        },
        headers={
            "X-User-ID": "test-user-id",
        },
    )
    knowledge_base_id = connect_repo_response.json()["knowledge_base_id"]

    # Configure validation to fail for the new token
    repo_validation_under_control.add_inaccessible_repository(
        url="https://github.com/test/repo",
        error_type="authentication_failed",
        status_code=401,
    )

    # When - Try to rotate with invalid token
    response = api_client.put(
        f"/repositories/{knowledge_base_id}/token",
        json={
            "access_token": "invalid-token",
        },
        headers={
            "X-User-ID": "test-user-id",
        },
    )

    # Then
    assert response.status_code == 401


def test_rotate_token_returns_400_when_payload_is_invalid(api_client):
    # When - Send request without access_token
    response = api_client.put(
        "/repositories/some-kb/token",
        json={},  # Missing access_token
        headers={
            "X-User-ID": "test-user-id",
        },
    )

    # Then
    assert response.status_code == 422  # FastAPI validation error
