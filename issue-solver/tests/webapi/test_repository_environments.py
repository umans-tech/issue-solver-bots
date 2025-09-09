import json

from tests.webapi.test_webapi import receive_event_message


def test_setup_environment_should_return_200_and_publish_environment_configuration_provided_event(
    api_client, sqs_client, sqs_queue, time_under_control
):
    # Given
    time_under_control.set_from_iso_format("2025-10-01T10:02:27")
    user_id = "test-user-id"
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/acme/awesome-repo",
            "access_token": "s3cr37-access-token",
            "space_id": "acme-space-01",
        },
        headers={
            "X-User-ID": user_id,
        },
    )
    receive_event_message(sqs_client, sqs_queue)
    knowledge_base_id = connect_repo_response.json()["knowledge_base_id"]
    environment_config = {
        "script": """
        #!/bin/bash
        apt update && apt install -y pip3 python3-pip
        curl -LsSf https://astral.sh/uv/install.sh | sh
        uv sync
        """
    }

    # When
    url = f"/repositories/{knowledge_base_id}/environments"
    response = api_client.post(
        url,
        json=environment_config,
        headers={
            "X-User-ID": user_id,
        },
    )

    # Then
    assert response.status_code == 201
    data = response.json()
    assert "environment_id" in data
    assert "process_id" in data

    process_id = response.json()["process_id"]
    process_response = api_client.get(f"/processes/{process_id}")
    assert process_response.status_code == 200
    process_data = process_response.json()
    assert process_data

    # Verify message was sent to SQS
    messages = receive_event_message(sqs_client, sqs_queue)
    assert "Messages" in messages
    message_body = json.loads(messages["Messages"][0]["Body"])
    assert message_body["type"] == "environment_configuration_provided"
    assert message_body["knowledge_base_id"] == knowledge_base_id
    assert message_body["user_id"] == user_id
    assert message_body["environment_id"] == data["environment_id"]
    assert message_body["script"] == environment_config["script"]


def test_setup_environment_should_return_404_when_repository_not_found(
    api_client, time_under_control
):
    # Given
    time_under_control.set_from_iso_format("2025-10-01T10:02:27")
    environment_config = {
        "script": """
        #!/bin/bash
        apt update && apt install -y pip3 python3-pip
        curl -LsSf https://astral.sh/uv/install.sh | sh
        uv sync
        """
    }

    # When
    url = "/repositories/nonexistent-kb/environments"
    response = api_client.post(
        url,
        json=environment_config,
        headers={
            "X-User-ID": "test-user-id",
        },
    )

    # Then
    assert response.status_code == 404
    assert "No repository found with knowledge base ID" in response.json()["detail"]
