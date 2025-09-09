import json

from tests.webapi.conftest import receive_event_message


def test_issue_resolution_route_should_request_issue_resolution_with_default_user(
    api_client, time_under_control, sqs_client, sqs_queue
):
    """Test issue resolution with default user_id when no header provided."""
    # Given
    current_time = "2025-01-01T10:10:56"
    time_under_control.set_from_iso_format(current_time)
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/test/repo",
            "access_token": "test-access-token",
            "user_id": "test-user-id",
            "space_id": "test-space-id",
        },
    )
    connect_repo_response_json = connect_repo_response.json()
    knowledge_base_id = connect_repo_response_json["knowledge_base_id"]
    receive_event_message(sqs_client, sqs_queue)

    # When
    response = api_client.post(
        "/resolutions/",
        json={
            "knowledgeBaseId": knowledge_base_id,
            "issue": {
                "description": "test-issue-description",
                "title": "test-issue-title",
            },
        },
    )

    # Then
    assert response.status_code == 201
    assert "processId" in response.json()
    process_id = response.json()["processId"]

    # Verify SQS message contains default user_id
    messages = receive_event_message(sqs_client, sqs_queue)
    assert "Messages" in messages
    message_body = json.loads(messages["Messages"][0]["Body"])
    assert message_body["process_id"] == process_id
    assert message_body["occurred_at"] == current_time
    assert message_body["type"] == "issue_resolution_requested"
    assert message_body["user_id"] == "unknown"

    # Verify process status
    get_process_response = api_client.get(f"/processes/{process_id}")
    assert get_process_response.status_code == 200
    assert get_process_response.json().get("status") == "requested"
    assert get_process_response.json().get("type") == "issue_resolution"


def test_issue_resolution_route_should_request_issue_resolution_with_user_header(
    api_client, time_under_control, sqs_client, sqs_queue
):
    """Test issue resolution with user_id from X-User-ID header."""
    # Given
    current_time = "2025-01-01T10:10:56"
    time_under_control.set_from_iso_format(current_time)
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/test/repo",
            "access_token": "test-access-token",
            "user_id": "test-user-id",
            "space_id": "test-space-id",
        },
    )
    connect_repo_response_json = connect_repo_response.json()
    knowledge_base_id = connect_repo_response_json["knowledge_base_id"]
    receive_event_message(sqs_client, sqs_queue)

    # When
    response = api_client.post(
        "/resolutions/",
        json={
            "knowledgeBaseId": knowledge_base_id,
            "issue": {
                "description": "test-issue-description",
                "title": "test-issue-title",
            },
        },
        headers={"X-User-ID": "john.doe@company.com"},
    )

    # Then
    assert response.status_code == 201
    assert "processId" in response.json()
    process_id = response.json()["processId"]

    # Verify SQS message contains actual user_id
    messages = receive_event_message(sqs_client, sqs_queue)
    assert "Messages" in messages
    message_body = json.loads(messages["Messages"][0]["Body"])
    assert message_body["process_id"] == process_id
    assert message_body["occurred_at"] == current_time
    assert message_body["type"] == "issue_resolution_requested"
    assert message_body["user_id"] == "john.doe@company.com"

    # Verify process status
    get_process_response = api_client.get(f"/processes/{process_id}")
    assert get_process_response.status_code == 200
    assert get_process_response.json().get("status") == "requested"
    assert get_process_response.json().get("type") == "issue_resolution"


def test_issue_resolution_route_should_handle_empty_user_header(
    api_client, time_under_control, sqs_client, sqs_queue
):
    """Test issue resolution with empty X-User-ID header falls back to default."""
    # Given
    current_time = "2025-01-01T10:10:56"
    time_under_control.set_from_iso_format(current_time)
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/test/repo",
            "access_token": "test-access-token",
            "user_id": "test-user-id",
            "space_id": "test-space-id",
        },
    )
    connect_repo_response_json = connect_repo_response.json()
    knowledge_base_id = connect_repo_response_json["knowledge_base_id"]
    receive_event_message(sqs_client, sqs_queue)

    # When
    response = api_client.post(
        "/resolutions/",
        json={
            "knowledgeBaseId": knowledge_base_id,
            "issue": {
                "description": "test-issue-description",
                "title": "test-issue-title",
            },
        },
        headers={"X-User-ID": ""},
    )

    # Then
    assert response.status_code == 201
    assert "processId" in response.json()

    # Verify SQS message falls back to default
    messages = receive_event_message(sqs_client, sqs_queue)
    assert "Messages" in messages
    message_body = json.loads(messages["Messages"][0]["Body"])
    assert message_body["user_id"] == "unknown"


def test_issue_resolution_route_should_request_issue_resolution_with_given_resolution_parameters(
    api_client, time_under_control, sqs_client, sqs_queue
):
    """Test issue resolution with user_id from X-User-ID header."""
    # Given
    current_time = "2025-09-01T10:10:56"
    time_under_control.set_from_iso_format(current_time)
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/test/repo",
            "accessToken": "test-access-token",
            "userId": "test-user-id",
            "spaceId": "test-space-id",
        },
    )
    connect_repo_response_json = connect_repo_response.json()
    knowledge_base_id = connect_repo_response_json["knowledge_base_id"]
    receive_event_message(sqs_client, sqs_queue)

    # When
    issue_title = "An annoying bug"
    issue_description = (
        "I noticed that when I click the button 'Submit', nothing happens."
    )
    response = api_client.post(
        "/resolutions/",
        json={
            "knowledgeBaseId": knowledge_base_id,
            "issue": {
                "title": issue_title,
                "description": issue_description,
            },
            "maxTurns": 55,
            "agent": "openai-tools",
            "aiModel": "gpt-5-mini",
            "aiModelVersion": "latest",
            "executionEnvironment": "ENV_REQUIRED",
        },
        headers={"X-User-ID": "johnny.doe@company.com"},
    )

    # Then
    assert response.status_code == 201
    assert "processId" in response.json()
    process_id = response.json()["processId"]

    # Verify SQS message contains actual user_id
    messages = receive_event_message(sqs_client, sqs_queue)
    assert "Messages" in messages
    message_body = json.loads(messages["Messages"][0]["Body"])
    assert message_body["process_id"] == process_id
    assert message_body["occurred_at"] == current_time
    assert message_body["type"] == "issue_resolution_requested"
    assert message_body["user_id"] == "johnny.doe@company.com"
    assert message_body["issue"]["title"] == issue_title
    assert message_body["issue"]["description"] == issue_description
    assert message_body["agent"] == "openai-tools"
    assert message_body["ai_model"] == "gpt-5-mini"
    assert message_body["ai_model_version"] == "latest"
    assert message_body["max_turns"] == 55
    assert message_body["execution_environment"] == "ENV_REQUIRED"

    # Verify process status
    get_process_response = api_client.get(f"/processes/{process_id}")
    assert get_process_response.status_code == 200
    assert get_process_response.json().get("status") == "requested"
    assert get_process_response.json().get("type") == "issue_resolution"
