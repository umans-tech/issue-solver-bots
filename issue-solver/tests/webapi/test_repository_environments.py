import json

import pytest
from tests.webapi.conftest import receive_event_message

from issue_solver.events.domain import EnvironmentConfigurationProvided
from issue_solver.events.serializable_records import deserialize


@pytest.mark.parametrize(
    "environment_config",
    [
        {
            "global": """
        apt update && apt install -y pip3 python3-pip
        curl -LsSf https://astral.sh/uv/install.sh | sh
        """,
            "project": """
        uv sync
        """,
        },
        {
            "script": """
        #!/bin/bash
        apt update && apt install -y pip3 python3-pip
        curl -LsSf https://astral.sh/uv/install.sh | sh
        uv sync
        """
        },
    ],
)
def test_setup_environment_should_return_200_and_publish_environment_configuration_provided_event(
    api_client, sqs_client, sqs_queue, time_under_control, environment_config
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
    api_response = response.json()
    assert "environment_id" in api_response
    assert "process_id" in api_response

    process_id = api_response["process_id"]
    process_response = api_client.get(f"/processes/{process_id}")
    assert process_response.status_code == 200
    assert process_response.json()

    # Verify message was sent to SQS
    messages = receive_event_message(sqs_client, sqs_queue)
    assert "Messages" in messages
    message_raw_body = messages["Messages"][0]["Body"]
    parsed_message = json.loads(message_raw_body)
    published_event = deserialize(parsed_message["type"], message_raw_body)
    assert published_event == EnvironmentConfigurationProvided(
        environment_id=api_response["environment_id"],
        knowledge_base_id=knowledge_base_id,
        user_id=user_id,
        global_setup=environment_config.get("global"),
        project_setup=environment_config.get("script")
        or environment_config.get("project"),
        process_id=process_id,
        occurred_at=time_under_control.now(),
    )


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
