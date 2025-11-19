import json

import pytest

from issue_solver.events.domain import DocumentationPromptsDefined
from issue_solver.events.serializable_records import deserialize
from tests.webapi.conftest import receive_event_message


def test_configure_auto_documentation_should_publish_event_and_create_process(
    api_client,
    time_under_control,
    sqs_client,
    sqs_queue,
):
    # Given
    time_under_control.set_from_iso_format("2025-11-01T09:05:00")
    user_id = "doc-bot@example.com"
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/acme/awesome-repo",
            "access_token": "s3cr37-access-token",
            "space_id": "acme-space-01",
        },
        headers={"X-User-ID": user_id},
    )
    assert connect_repo_response.status_code == 201
    receive_event_message(sqs_client, sqs_queue)
    knowledge_base_id = connect_repo_response.json()["knowledge_base_id"]

    prompts_payload = {
        "docsPrompts": {
            "runbook": "Produce a runbook for operating the service during incidents.",
            "api": "Summarize the public API surface with request/response pairs.",
        }
    }

    # When
    response = api_client.post(
        f"/repositories/{knowledge_base_id}/auto-documentation",
        json=prompts_payload,
        headers={"X-User-ID": user_id},
    )

    # Then
    assert response.status_code == 201
    body = response.json()
    assert body["knowledge_base_id"] == knowledge_base_id
    assert body["docs_prompts"] == prompts_payload["docsPrompts"]

    process_id = body["process_id"]
    event_message = receive_event_message(sqs_client, sqs_queue)
    assert "Messages" in event_message
    raw_body = event_message["Messages"][0]["Body"]
    parsed = json.loads(raw_body)
    assert parsed["type"] == "documentation_prompts_defined"
    published_event = deserialize(parsed["type"], raw_body)
    assert isinstance(published_event, DocumentationPromptsDefined)
    assert published_event.docs_prompts == prompts_payload["docsPrompts"]
    assert published_event.process_id == process_id

    process_response = api_client.get(f"/processes/{process_id}")
    assert process_response.status_code == 200
    process_json = process_response.json()
    assert process_json["type"] == "docs_setup"
    assert process_json["status"] == "configured"
    assert process_json["events"][0]["type"] == "documentation_prompts_defined"


@pytest.mark.parametrize(
    "docs_prompts",
    [
        {"docsPrompts": {"glossary": "Document important domain events"}},
    ],
)
def test_configure_auto_documentation_should_return_404_when_repository_missing(
    api_client, docs_prompts
):
    # When
    response = api_client.post(
        "/repositories/nonexistent-kb/auto-documentation",
        json=docs_prompts,
        headers={"X-User-ID": "doc-bot@example.com"},
    )

    # Then
    assert response.status_code == 404
    assert "No repository found" in response.json()["detail"]


def test_get_auto_documentation_should_return_latest_prompts(
    api_client,
    time_under_control,
    sqs_client,
    sqs_queue,
):
    time_under_control.set_from_iso_format("2025-11-02T08:00:00")
    user_id = "prompts@example.com"
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/acme/awesome-repo",
            "access_token": "s3cr37-access-token",
            "space_id": "acme-space-01",
        },
        headers={"X-User-ID": user_id},
    )
    assert connect_repo_response.status_code == 201
    receive_event_message(sqs_client, sqs_queue)
    knowledge_base_id = connect_repo_response.json()["knowledge_base_id"]

    payload = {
        "docsPrompts": {
            "overview": "Create a concise overview for leadership updates.",
            "adr": "Capture architecture trade-offs and choices.",
        }
    }
    post_response = api_client.post(
        f"/repositories/{knowledge_base_id}/auto-documentation",
        json=payload,
        headers={"X-User-ID": user_id},
    )
    assert post_response.status_code == 201
    receive_event_message(sqs_client, sqs_queue)

    get_response = api_client.get(
        f"/repositories/{knowledge_base_id}/auto-documentation",
        headers={"X-User-ID": user_id},
    )
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["knowledge_base_id"] == knowledge_base_id
    assert data["docs_prompts"] == payload["docsPrompts"]
    assert data["updated_at"] is not None
    assert data["last_process_id"] is not None


def test_auto_documentation_configuration_maintains_continuous_process(
    api_client,
    time_under_control,
    sqs_client,
    sqs_queue,
):
    time_under_control.set_from_iso_format("2025-11-02T10:30:00")
    user_id = "doc-bot@example.com"

    # Given
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/acme/awesome-repo",
            "access_token": "s3cr37-access-token",
            "space_id": "acme-space-01",
        },
        headers={"X-User-ID": user_id},
    )
    assert connect_repo_response.status_code == 201
    receive_event_message(sqs_client, sqs_queue)
    knowledge_base_id = connect_repo_response.json()["knowledge_base_id"]

    first_payload = {
        "docsPrompts": {
            "overview": "Generate an overview document",
        }
    }
    second_payload = {
        "docsPrompts": {
            "overview": "Refresh the overview with metrics",
            "adr": "Capture recent architectural trade-offs",
        }
    }

    first_response = api_client.post(
        f"/repositories/{knowledge_base_id}/auto-documentation",
        json=first_payload,
        headers={"X-User-ID": user_id},
    )
    assert first_response.status_code == 201
    first_process_id = first_response.json()["process_id"]
    receive_event_message(sqs_client, sqs_queue)

    # When
    second_response = api_client.post(
        f"/repositories/{knowledge_base_id}/auto-documentation",
        json=second_payload,
        headers={"X-User-ID": user_id},
    )
    assert second_response.status_code == 201
    second_process_id = second_response.json()["process_id"]

    # Then
    assert second_process_id == first_process_id
    assert second_response.json()["docs_prompts"] == second_payload["docsPrompts"]


def test_auto_documentation_prompt_can_be_removed(
    api_client,
    time_under_control,
    sqs_client,
    sqs_queue,
):
    time_under_control.set_from_iso_format("2025-11-03T08:00:00")
    user_id = "prompts@example.com"
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/acme/awesome-repo",
            "access_token": "s3cr37-access-token",
            "space_id": "acme-space-01",
        },
        headers={"X-User-ID": user_id},
    )
    assert connect_repo_response.status_code == 201
    receive_event_message(sqs_client, sqs_queue)
    knowledge_base_id = connect_repo_response.json()["knowledge_base_id"]

    post_response = api_client.post(
        f"/repositories/{knowledge_base_id}/auto-documentation",
        json={
            "docsPrompts": {
                "glossary": "Document the glossary",
                "setup": "Create a setup guide",
            }
        },
        headers={"X-User-ID": user_id},
    )
    assert post_response.status_code == 201
    receive_event_message(sqs_client, sqs_queue)

    update_response = api_client.post(
        f"/repositories/{knowledge_base_id}/auto-documentation",
        json={
            "docsPrompts": {
                "setup": "Update the setup guide with troubleshooting tips",
            }
        },
        headers={"X-User-ID": user_id},
    )
    assert update_response.status_code == 201
    receive_event_message(sqs_client, sqs_queue)

    removal_response = api_client.request(
        "DELETE",
        f"/repositories/{knowledge_base_id}/auto-documentation",
        json={"promptIds": ["glossary", "glossary"]},
        headers={"X-User-ID": user_id},
    )
    assert removal_response.status_code == 200
    assert removal_response.json()["deleted_prompt_ids"] == ["glossary"]
    removal_event = receive_event_message(sqs_client, sqs_queue)
    parsed = json.loads(removal_event["Messages"][0]["Body"])
    published_event = deserialize(parsed["type"], removal_event["Messages"][0]["Body"])
    assert published_event.prompt_ids == {"glossary"}
    assert parsed["type"] == "documentation_prompts_removed"

    get_response = api_client.get(
        f"/repositories/{knowledge_base_id}/auto-documentation",
        headers={"X-User-ID": user_id},
    )
    data = get_response.json()
    assert "glossary" not in data["docs_prompts"]
    assert (
        data["docs_prompts"]["setup"]
        == "Update the setup guide with troubleshooting tips"
    )


def test_delete_auto_documentation_prompts_should_fail_when_none_defined(
    api_client,
    time_under_control,
    sqs_client,
    sqs_queue,
):
    # Given
    time_under_control.set_from_iso_format("2025-11-04T09:00:00")
    user_id = "doc-bot@example.com"
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/acme/awesome-repo",
            "access_token": "s3cr37-access-token",
            "space_id": "acme-space-01",
        },
        headers={"X-User-ID": user_id},
    )
    assert connect_repo_response.status_code == 201
    receive_event_message(sqs_client, sqs_queue)
    knowledge_base_id = connect_repo_response.json()["knowledge_base_id"]

    # When
    response = api_client.request(
        "DELETE",
        f"/repositories/{knowledge_base_id}/auto-documentation",
        json={"promptIds": ["overview"]},
        headers={"X-User-ID": user_id},
    )

    # Then
    assert response.status_code == 404
    assert knowledge_base_id in response.json()["detail"]
    assert "Cannot remove auto-documentation prompts" in response.json()["detail"]


def test_delete_auto_documentation_prompts_should_fail_when_prompt_unknown(
    api_client,
    time_under_control,
    sqs_client,
    sqs_queue,
):
    # Given
    time_under_control.set_from_iso_format("2025-11-04T10:00:00")
    user_id = "doc-bot@example.com"
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/acme/awesome-repo",
            "access_token": "s3cr37-access-token",
            "space_id": "acme-space-01",
        },
        headers={"X-User-ID": user_id},
    )
    assert connect_repo_response.status_code == 201
    receive_event_message(sqs_client, sqs_queue)
    knowledge_base_id = connect_repo_response.json()["knowledge_base_id"]

    post_response = api_client.post(
        f"/repositories/{knowledge_base_id}/auto-documentation",
        json={
            "docsPrompts": {
                "overview": "Write overview",
            }
        },
        headers={"X-User-ID": user_id},
    )
    assert post_response.status_code == 201
    receive_event_message(sqs_client, sqs_queue)

    # When
    response = api_client.request(
        "DELETE",
        f"/repositories/{knowledge_base_id}/auto-documentation",
        json={"promptIds": ["unknown"]},
        headers={"X-User-ID": user_id},
    )

    # Then
    assert response.status_code == 404
    assert "unknown" in response.json()["detail"]
