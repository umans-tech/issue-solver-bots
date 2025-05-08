import json

from tests.webapi.test_webapi import receive_event_message


def test_issue_resolution_route_should_request_issue_resolution(
    api_client, time_under_control, sqs_client, sqs_queue
):
    # Given
    time_under_control.set_from_iso_format("2021-01-01T00:00:00")
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
    assert "process_id" in response.json()
    process_id = response.json()["process_id"]
    messages = receive_event_message(sqs_client, sqs_queue)
    assert "Messages" in messages
    message_body = json.loads(messages["Messages"][0]["Body"])
    assert message_body["process_id"] == process_id
    assert message_body["occurred_at"] == "2021-01-01T00:00:00"
    assert message_body["type"] == "issue_resolution_requested"
    get_process_response = api_client.get(
        f"/processes/{process_id}",
    )
    assert get_process_response.status_code == 200
    assert get_process_response.json().get("status") == "requested"
    assert get_process_response.json().get("type") == "issue_resolution"
