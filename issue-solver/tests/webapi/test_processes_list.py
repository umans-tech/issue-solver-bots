from fastapi.testclient import TestClient
from issue_solver.webapi.main import app
from issue_solver.webapi.routers import notion_integration

client = TestClient(app)


def test_returns_empty_list_when_no_processes_exist(api_client):
    # When
    response = api_client.get("/processes")

    # Then
    assert response.status_code == 200
    data = response.json()
    assert data["processes"] == []
    assert data["total"] == 0
    assert data["limit"] == 50
    assert data["offset"] == 0


def test_returns_processes_filtered_by_space_id(api_client, time_under_control):
    # Given
    time_under_control.set_from_iso_format("2021-01-01T00:00:00")

    # Create a repository process with space_id
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/test/repo",
            "access_token": "test-access-token",
            "user_id": "test-user-id",
            "space_id": "test-space-id",
        },
    )
    assert connect_repo_response.status_code == 201

    # When
    response = api_client.get("/processes?space_id=test-space-id")

    # Then
    assert response.status_code == 200
    data = response.json()
    assert len(data["processes"]) == 1
    assert data["processes"][0]["type"] == "code_repository_integration"
    assert data["total"] == 1


def test_returns_processes_filtered_by_knowledge_base_id(
    api_client, time_under_control
):
    # Given
    time_under_control.set_from_iso_format("2021-01-01T00:00:00")

    # Create a repository process to get a knowledge_base_id
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/test/repo",
            "access_token": "test-access-token",
            "user_id": "test-user-id",
            "space_id": "test-space-id",
        },
    )
    assert connect_repo_response.status_code == 201
    knowledge_base_id = connect_repo_response.json()["knowledge_base_id"]

    # Create an issue resolution process with the same knowledge_base_id
    issue_response = api_client.post(
        "/resolutions/",
        json={
            "knowledgeBaseId": knowledge_base_id,
            "issue": {
                "description": "test-issue-description",
                "title": "test-issue-title",
            },
        },
    )
    assert issue_response.status_code == 201

    # When
    response = api_client.get(f"/processes?knowledge_base_id={knowledge_base_id}")

    # Then
    assert response.status_code == 200
    data = response.json()
    assert len(data["processes"]) == 2  # repository + issue resolution
    assert data["total"] == 2

    # Check we have both process types
    process_types = [p["type"] for p in data["processes"]]
    assert "code_repository_integration" in process_types
    assert "issue_resolution" in process_types


def test_returns_processes_filtered_by_process_type(api_client, time_under_control):
    # Given
    time_under_control.set_from_iso_format("2021-01-01T00:00:00")

    # Create a repository process
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/test/repo",
            "access_token": "test-access-token",
            "user_id": "test-user-id",
            "space_id": "test-space-id",
        },
    )
    assert connect_repo_response.status_code == 201
    knowledge_base_id = connect_repo_response.json()["knowledge_base_id"]

    # Create an issue resolution process
    issue_response = api_client.post(
        "/resolutions/",
        json={
            "knowledgeBaseId": knowledge_base_id,
            "issue": {
                "description": "test-issue-description",
                "title": "test-issue-title",
            },
        },
    )
    assert issue_response.status_code == 201

    # When - Filter by repository process type
    response = api_client.get("/processes?process_type=code_repository_integration")

    # Then
    assert response.status_code == 200
    data = response.json()
    assert len(data["processes"]) == 1
    assert data["processes"][0]["type"] == "code_repository_integration"
    assert data["total"] == 1

    # When - Filter by issue resolution process type
    response = api_client.get("/processes?process_type=issue_resolution")

    # Then
    assert response.status_code == 200
    data = response.json()
    assert len(data["processes"]) == 1
    assert data["processes"][0]["type"] == "issue_resolution"
    assert data["total"] == 1


def test_returns_processes_filtered_by_status(api_client, time_under_control):
    # Given
    time_under_control.set_from_iso_format("2021-01-01T00:00:00")

    # Create a repository process (will have status "connected")
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/test/repo",
            "access_token": "test-access-token",
            "user_id": "test-user-id",
            "space_id": "test-space-id",
        },
    )
    assert connect_repo_response.status_code == 201
    knowledge_base_id = connect_repo_response.json()["knowledge_base_id"]

    # Create an issue resolution process (will have status "requested")
    issue_response = api_client.post(
        "/resolutions/",
        json={
            "knowledgeBaseId": knowledge_base_id,
            "issue": {
                "description": "test-issue-description",
                "title": "test-issue-title",
            },
        },
    )
    assert issue_response.status_code == 201

    # When - Filter by "connected" status
    response = api_client.get("/processes?status=connected")

    # Then
    assert response.status_code == 200
    data = response.json()
    assert len(data["processes"]) == 1
    assert data["processes"][0]["status"] == "connected"
    assert data["processes"][0]["type"] == "code_repository_integration"
    assert data["total"] == 1

    # When - Filter by "requested" status
    response = api_client.get("/processes?status=requested")

    # Then
    assert response.status_code == 200
    data = response.json()
    assert len(data["processes"]) == 1
    assert data["processes"][0]["status"] == "requested"
    assert data["processes"][0]["type"] == "issue_resolution"
    assert data["total"] == 1


def test_returns_auto_documentation_process(api_client, time_under_control):
    # Given
    time_under_control.set_from_iso_format("2025-11-01T12:00:00")
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/test/repo",
            "access_token": "test-access-token",
            "user_id": "test-user-id",
            "space_id": "test-space-id",
        },
        headers={"X-User-ID": "test-user-id"},
    )
    assert connect_repo_response.status_code == 201
    knowledge_base_id = connect_repo_response.json()["knowledge_base_id"]

    auto_doc_response = api_client.post(
        f"/repositories/{knowledge_base_id}/auto-documentation",
        json={
            "docsPrompts": {
                "overview": "Generate an overview document",
            }
        },
        headers={"X-User-ID": "test-user-id"},
    )
    assert auto_doc_response.status_code == 201

    # When
    response = api_client.get("/processes?process_type=docs_setup")

    # Then
    assert response.status_code == 200
    data = response.json()
    assert len(data["processes"]) == 1
    process = data["processes"][0]
    assert process["type"] == "docs_setup"
    assert process["status"] == "configured"


def test_auto_documentation_process_list_deduplicates_events(
    api_client, time_under_control
):
    # Given
    time_under_control.set_from_iso_format("2025-11-01T12:00:00")
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/test/repo",
            "access_token": "test-access-token",
            "user_id": "test-user-id",
            "space_id": "test-space-id",
        },
        headers={"X-User-ID": "test-user-id"},
    )
    assert connect_repo_response.status_code == 201
    knowledge_base_id = connect_repo_response.json()["knowledge_base_id"]

    api_client.post(
        f"/repositories/{knowledge_base_id}/auto-documentation",
        json={
            "docsPrompts": {
                "overview": "Generate an overview document",
            }
        },
        headers={"X-User-ID": "test-user-id"},
    )
    api_client.post(
        f"/repositories/{knowledge_base_id}/auto-documentation",
        json={
            "docsPrompts": {
                "overview": "Refresh the overview",
            }
        },
        headers={"X-User-ID": "test-user-id"},
    )
    api_client.request(
        "DELETE",
        f"/repositories/{knowledge_base_id}/auto-documentation",
        json={"promptIds": ["overview"]},
        headers={"X-User-ID": "test-user-id"},
    )

    # When
    response = api_client.get("/processes?process_type=docs_setup")

    # Then
    assert response.status_code == 200
    data = response.json()
    assert len(data["processes"]) == 1
    assert data["processes"][0]["status"] == "removed"


def test_returns_notion_integration_process(
    api_client, time_under_control, monkeypatch
):
    time_under_control.set_from_iso_format("2025-01-05T08:00:00")

    notion_integration._get_mcp_settings.cache_clear()
    monkeypatch.setenv("NOTION_MCP_CLIENT_ID", "stub-mcp-client-id")
    monkeypatch.setenv("NOTION_MCP_CLIENT_SECRET", "stub-mcp-client-secret")
    monkeypatch.setenv(
        "NOTION_MCP_OAUTH_REDIRECT_URI",
        "https://example.com/notion/mcp/callback",
    )
    monkeypatch.setenv("NOTION_MCP_RETURN_BASE_URL", "https://frontend.example.com")

    async def fake_request_oauth_token(
        *,
        payload,
        logger,
        endpoint,
        client_id,
        client_secret,
        auth_method,
        form_encode=False,
    ):
        grant_type = payload.get("grant_type")
        if (
            endpoint == "https://mcp.notion.com/token"
            and grant_type == "authorization_code"
        ):
            return {
                "access_token": "mcp-access-token",
                "refresh_token": "mcp-refresh-token",
                "expires_in": 3600,
                "workspace_id": "workspace-123",
                "workspace_name": "Acme Workspace",
                "bot_id": "bot-abc",
            }
        raise AssertionError(f"Unexpected grant type: {grant_type}")

    monkeypatch.setattr(
        notion_integration,
        "_request_oauth_token",
        fake_request_oauth_token,
    )

    start_resp = api_client.get(
        "/integrations/notion/oauth/mcp/start",
        params={"space_id": "brice-space-001"},
        headers={"X-User-ID": "brice-user-001"},
    )
    state = start_resp.json()["state"]

    api_client.get(
        "/integrations/notion/mcp/oauth/callback",
        params={"code": "auth-code", "state": state},
        headers={"X-User-ID": "brice-user-001"},
        follow_redirects=False,
    )

    response = api_client.get("/processes?space_id=brice-space-001")
    assert response.status_code == 200
    data = response.json()
    notion_processes = [
        p for p in data["processes"] if p["type"] == "notion_integration"
    ]

    assert len(notion_processes) == 1
    notion_process = notion_processes[0]
    assert notion_process["status"] == "connected"
    events = notion_process["events"]
    assert events, "expected at least one event for Notion integration process"
    first_event = events[0]
    assert first_event["type"] == "notion_integration_authorized"
    assert first_event["space_id"] == "brice-space-001"
    assert first_event["workspace_id"] == "workspace-123"
    assert first_event["workspace_name"] == "Acme Workspace"


def test_returns_processes_with_default_pagination(api_client, time_under_control):
    # Given
    time_under_control.set_from_iso_format("2021-01-01T00:00:00")

    # Create multiple processes to test pagination
    for i in range(3):
        api_client.post(
            "/repositories/",
            json={
                "url": f"https://github.com/test/repo{i}",
                "access_token": "test-access-token",
                "user_id": "test-user-id",
                "space_id": "test-space-id",
            },
        )

    # When - No pagination parameters provided
    response = api_client.get("/processes?space_id=test-space-id")

    # Then - Should use default pagination
    assert response.status_code == 200
    data = response.json()
    assert len(data["processes"]) == 3  # All processes returned
    assert data["total"] == 3
    assert data["limit"] == 50  # Default limit
    assert data["offset"] == 0  # Default offset

    # Verify pagination fields are present in response
    assert "limit" in data
    assert "offset" in data
    assert "total" in data


def test_returns_processes_with_custom_limit(api_client, time_under_control):
    # Given
    time_under_control.set_from_iso_format("2021-01-01T00:00:00")

    # Create 5 processes
    for i in range(5):
        api_client.post(
            "/repositories/",
            json={
                "url": f"https://github.com/test/repo{i}",
                "access_token": "test-access-token",
                "user_id": "test-user-id",
                "space_id": "test-space-id",
            },
        )

    # When - Request with custom limit
    response = api_client.get("/processes?space_id=test-space-id&limit=3")

    # Then
    assert response.status_code == 200
    data = response.json()
    assert len(data["processes"]) == 3  # Limited to 3
    assert data["total"] == 5  # Total available is still 5
    assert data["limit"] == 3  # Custom limit applied
    assert data["offset"] == 0  # Default offset


def test_returns_processes_with_multiple_filters_combined_space_id_and_process_type(
    api_client, time_under_control
):
    # Given
    time_under_control.set_from_iso_format("2021-01-01T00:00:00")

    # Create repository process in test-space-id
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/test/repo",
            "access_token": "test-access-token",
            "user_id": "test-user-id",
            "space_id": "test-space-id",
        },
    )
    assert connect_repo_response.status_code == 201
    knowledge_base_id = connect_repo_response.json()["knowledge_base_id"]

    # Create issue resolution process in same space (via knowledge_base_id)
    issue_response = api_client.post(
        "/resolutions/",
        json={
            "knowledgeBaseId": knowledge_base_id,
            "issue": {
                "description": "test-issue-description",
                "title": "test-issue-title",
            },
        },
    )
    assert issue_response.status_code == 201

    # Create repository process in different space
    api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/test/other-repo",
            "access_token": "test-access-token",
            "user_id": "test-user-id",
            "space_id": "other-space-id",
        },
    )

    # When - Filter by space_id AND process_type
    response = api_client.get(
        "/processes?space_id=test-space-id&process_type=code_repository_integration"
    )

    # Then - Should only return repository process from test-space-id
    assert response.status_code == 200
    data = response.json()
    assert len(data["processes"]) == 1
    assert data["processes"][0]["type"] == "code_repository_integration"
    assert data["total"] == 1

    # When - Filter by space_id AND different process_type
    response = api_client.get(
        "/processes?space_id=test-space-id&process_type=issue_resolution"
    )

    # Then - Should return empty (issue resolution not directly linked to space_id)
    assert response.status_code == 200
    data = response.json()
    assert len(data["processes"]) == 0
    assert data["total"] == 0


def test_returns_processes_with_multiple_filters_combined_knowledge_base_id_and_status(
    api_client, time_under_control
):
    # Given
    time_under_control.set_from_iso_format("2021-01-01T00:00:00")

    # Create repository process
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/test/repo",
            "access_token": "test-access-token",
            "user_id": "test-user-id",
            "space_id": "test-space-id",
        },
    )
    assert connect_repo_response.status_code == 201
    knowledge_base_id = connect_repo_response.json()["knowledge_base_id"]

    # Create issue resolution process with same knowledge_base_id
    issue_response = api_client.post(
        "/resolutions/",
        json={
            "knowledgeBaseId": knowledge_base_id,
            "issue": {
                "description": "test-issue-description",
                "title": "test-issue-title",
            },
        },
    )
    assert issue_response.status_code == 201

    # When - Filter by knowledge_base_id AND status "connected"
    response = api_client.get(
        f"/processes?knowledge_base_id={knowledge_base_id}&status=connected"
    )

    # Then - Should only return repository process (status=connected)
    assert response.status_code == 200
    data = response.json()
    assert len(data["processes"]) == 1
    assert data["processes"][0]["type"] == "code_repository_integration"
    assert data["processes"][0]["status"] == "connected"
    assert data["total"] == 1

    # When - Filter by knowledge_base_id AND status "requested"
    response = api_client.get(
        f"/processes?knowledge_base_id={knowledge_base_id}&status=requested"
    )

    # Then - Should only return issue resolution process (status=requested)
    assert response.status_code == 200
    data = response.json()
    assert len(data["processes"]) == 1
    assert data["processes"][0]["type"] == "issue_resolution"
    assert data["processes"][0]["status"] == "requested"
    assert data["total"] == 1


def test_returns_processes_with_custom_offset(api_client, time_under_control):
    # Given
    time_under_control.set_from_iso_format("2021-01-01T00:00:00")

    # Create 5 processes
    for i in range(5):
        api_client.post(
            "/repositories/",
            json={
                "url": f"https://github.com/test/repo{i}",
                "access_token": "test-access-token",
                "user_id": "test-user-id",
                "space_id": "test-space-id",
            },
        )

    # When - Request with custom offset
    response = api_client.get("/processes?space_id=test-space-id&offset=2")

    # Then
    assert response.status_code == 200
    data = response.json()
    assert len(data["processes"]) == 3  # 5 total - 2 offset = 3 remaining
    assert data["total"] == 5  # Total available is still 5
    assert data["limit"] == 50  # Default limit
    assert data["offset"] == 2  # Custom offset applied


def test_returns_processes_with_both_limit_and_offset(api_client, time_under_control):
    # Given
    time_under_control.set_from_iso_format("2021-01-01T00:00:00")

    # Create 10 processes
    for i in range(10):
        api_client.post(
            "/repositories/",
            json={
                "url": f"https://github.com/test/repo{i}",
                "access_token": "test-access-token",
                "user_id": "test-user-id",
                "space_id": "test-space-id",
            },
        )

    # When - Request with both limit and offset
    response = api_client.get("/processes?space_id=test-space-id&limit=3&offset=2")

    # Then
    assert response.status_code == 200
    data = response.json()
    assert len(data["processes"]) == 3  # Limited to 3
    assert data["total"] == 10  # Total available is 10
    assert data["limit"] == 3  # Custom limit applied
    assert data["offset"] == 2  # Custom offset applied

    # When - Request beyond available data
    response = api_client.get("/processes?space_id=test-space-id&limit=5&offset=8")

    # Then - Should return only remaining processes
    assert response.status_code == 200
    data = response.json()
    assert len(data["processes"]) == 2
    assert data["total"] == 10
    assert data["limit"] == 5
    assert data["offset"] == 8


def test_handles_non_existent_knowledge_base_id_gracefully(
    api_client, time_under_control
):
    # Given
    time_under_control.set_from_iso_format("2021-01-01T00:00:00")

    # Create some processes with real knowledge_base_ids
    connect_repo_response = api_client.post(
        "/repositories/",
        json={
            "url": "https://github.com/test/repo",
            "access_token": "test-access-token",
            "user_id": "test-user-id",
            "space_id": "test-space-id",
        },
    )
    assert connect_repo_response.status_code == 201

    # When - Query with non-existent knowledge_base_id
    response = api_client.get("/processes?knowledge_base_id=non-existent-kb-id")

    # Then - Should return empty list gracefully
    assert response.status_code == 200
    data = response.json()
    assert data["processes"] == []
    assert data["total"] == 0
    assert data["limit"] == 50
    assert data["offset"] == 0
