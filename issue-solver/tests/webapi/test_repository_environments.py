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


def test_get_latest_environment_should_return_404_when_no_environment(
    api_client, time_under_control, sqs_client, sqs_queue
):
    # Given a connected repository but no environment yet
    time_under_control.set_from_iso_format("2025-10-01T10:10:00")
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
    url = f"/repositories/{knowledge_base_id}/environments/latest"
    response = api_client.get(url)

    # Then
    assert response.status_code == 404
    assert "No environment found" in response.json()["detail"]


def test_get_latest_environment_should_return_existing_configuration_when_only_one(
    api_client, time_under_control, sqs_client, sqs_queue
):
    # Given
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
    knowledge_base_id = connect_repo_response.json()["knowledge_base_id"]

    time_under_control.set_from_iso_format("2025-10-01T09:00:00")
    second_env = {
        "script": "#!/bin/bash\necho later setup",
    }
    environment_response = api_client.post(
        f"/repositories/{knowledge_base_id}/environments",
        json=second_env,
        headers={"X-User-ID": user_id},
    )
    assert environment_response.status_code == 201
    environment_json = environment_response.json()

    # When
    latest_resp = api_client.get(
        f"/repositories/{knowledge_base_id}/environments/latest"
    )

    # Then
    assert latest_resp.status_code == 200
    latest = latest_resp.json()
    assert latest["environment_id"] == environment_json["environment_id"]
    assert latest["process_id"] == environment_json["process_id"]
    assert latest["occurred_at"] == "2025-10-01T09:00:00"


def test_get_latest_environment_should_return_latest_configuration(
    api_client, time_under_control, sqs_client, sqs_queue
):
    # Given
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
    knowledge_base_id = connect_repo_response.json()["knowledge_base_id"]

    # First environment at t1
    time_under_control.set_from_iso_format("2025-10-01T08:00:00")
    first_env = {
        "global": "apt update && apt install -y python3",
        "project": "uv sync",
    }
    first_environment_creation_response = api_client.post(
        f"/repositories/{knowledge_base_id}/environments",
        json=first_env,
        headers={"X-User-ID": user_id},
    )
    assert first_environment_creation_response.status_code == 201

    # Second environment at t2 (later)
    time_under_control.set_from_iso_format("2025-10-01T09:00:00")
    second_env = {
        "global": "#!/bin/bash\necho 'later global setup'",
        "project": "#!/bin/bash\necho 'later project setup'",
    }
    second_environment_creation_response = api_client.post(
        f"/repositories/{knowledge_base_id}/environments",
        json=second_env,
        headers={"X-User-ID": user_id},
    )
    assert second_environment_creation_response.status_code == 201
    second_environment_creation_json = second_environment_creation_response.json()

    # When
    latest_resp = api_client.get(
        f"/repositories/{knowledge_base_id}/environments/latest"
    )

    # Then
    assert latest_resp.status_code == 200
    latest = latest_resp.json()
    assert (
        latest["environment_id"] == second_environment_creation_json["environment_id"]
    )
    assert latest["process_id"] == second_environment_creation_json["process_id"]
    assert latest["occurred_at"] == "2025-10-01T09:00:00"
    assert latest["global"] == second_env["global"]
    assert latest["project"] == second_env["project"]


def test_get_latest_environment_unknown_kb_should_return_404(api_client):
    # When
    response = api_client.get("/repositories/nonexistent-kb/environments/latest")

    # Then
    assert response.status_code == 404
    assert "No environment found" in response.json()["detail"]
