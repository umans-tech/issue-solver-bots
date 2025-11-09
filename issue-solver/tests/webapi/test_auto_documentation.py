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
    assert process_json["type"] == "auto_documentation"
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
