"""Tests for Notion MCP proxy functionality."""

from datetime import UTC, datetime, timedelta

import pytest
from starlette.testclient import TestClient

from issue_solver.events.notion_integration import NotionCredentials
from issue_solver.webapi.routers import mcp_notion_proxy, notion_integration


@pytest.fixture(autouse=True)
def stub_notion_validation(monkeypatch):
    async def fake_validate(_token: str) -> dict:
        return {
            "object": "user",
            "id": "bot-id",
            "bot": {
                "workspace_id": "workspace-123",
                "workspace_name": "Acme Workspace",
            },
        }

    monkeypatch.setattr(notion_integration, "_validate_notion_token", fake_validate)
    yield
    monkeypatch.delattr(notion_integration, "_validate_notion_token")


def test_mcp_notion_proxy_initialize(api_client: TestClient, monkeypatch):
    """Test that MCP initialize handshake works."""
    space_id = "space-with-notion"

    credentials = NotionCredentials(
        access_token="secret-token",
        refresh_token=None,
        token_expires_at=None,
        workspace_id="workspace-123",
        workspace_name="Acme Workspace",
        bot_id="bot-id",
        process_id="process-secret",
        auth_mode="oauth",
    )

    async def fake_get_credentials(event_store, requested_space_id):
        return credentials

    async def fake_ensure_fresh_credentials(**_kwargs):
        return credentials

    monkeypatch.setattr(
        mcp_notion_proxy, "get_notion_credentials", fake_get_credentials
    )
    monkeypatch.setattr(
        mcp_notion_proxy,
        "ensure_fresh_notion_credentials",
        fake_ensure_fresh_credentials,
    )

    payload = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "id": 1,
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
        "meta": {
            "user_id": "user-123",
            "space_id": space_id,
        },
    }

    response = api_client.post("/mcp/notion/proxy", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert data["result"]["protocolVersion"] == "2024-11-05"
    assert "capabilities" in data["result"]
    assert "serverInfo" in data["result"]
    assert data["result"]["serverInfo"]["name"] == "notion-mcp-proxy"


def test_mcp_notion_proxy_missing_space_id(api_client: TestClient):
    """Test that missing space_id returns an error."""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1,
        "meta": {
            "user_id": "user-123",
        },
    }

    response = api_client.post("/mcp/notion/proxy", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert "space_id" in data["error"]["message"]


def test_mcp_notion_proxy_no_integration(api_client: TestClient):
    """Test that missing Notion integration returns an error."""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1,
        "meta": {
            "user_id": "user-123",
            "space_id": "space-without-notion",
        },
    }

    response = api_client.post("/mcp/notion/proxy", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert "No Notion integration" in data["error"]["message"]


def test_mcp_notion_proxy_tools_list(api_client: TestClient, monkeypatch):
    """Test that tools/list returns available Notion tools."""
    space_id = "space-with-notion"

    credentials = NotionCredentials(
        access_token="secret-token",
        refresh_token="refresh-secret",
        token_expires_at=datetime.now(UTC) + timedelta(hours=1),
        workspace_id="workspace-123",
        workspace_name="Acme Workspace",
        bot_id="bot-id",
        process_id="process-secret",
        auth_mode="oauth",
    )

    async def fake_get_credentials(event_store, requested_space_id):
        assert requested_space_id == space_id
        return credentials

    async def fake_ensure_fresh_credentials(**_kwargs):
        return credentials

    monkeypatch.setattr(
        mcp_notion_proxy, "get_notion_credentials", fake_get_credentials
    )
    monkeypatch.setattr(
        mcp_notion_proxy,
        "ensure_fresh_notion_credentials",
        fake_ensure_fresh_credentials,
    )

    payload = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1,
        "meta": {
            "user_id": "user-123",
            "space_id": space_id,
        },
    }

    response = api_client.post("/mcp/notion/proxy", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "tools" in data["result"]
    tools = data["result"]["tools"]
    assert len(tools) == 6
    tool_names = [t["name"] for t in tools]
    assert "notion_search" in tool_names
    assert "notion_get_page" in tool_names
    assert "notion_get_block_children" in tool_names
    assert "notion_list_databases" in tool_names
    assert "notion_get_database" in tool_names
    assert "notion_query_database" in tool_names


def test_mcp_notion_proxy_search_tool(api_client: TestClient, monkeypatch):
    """Test that notion_search tool calls Notion API correctly."""
    space_id = "space-with-notion"
    search_query = "product requirements"

    credentials = NotionCredentials(
        access_token="secret-token",
        refresh_token=None,
        token_expires_at=None,
        workspace_id="workspace-123",
        workspace_name="Acme Workspace",
        bot_id="bot-id",
        process_id="process-secret",
        auth_mode="oauth",
    )

    async def fake_get_credentials(event_store, requested_space_id):
        return credentials

    async def fake_ensure_fresh_credentials(**_kwargs):
        return credentials

    # Mock the Notion API call
    fake_notion_response = {
        "results": [
            {
                "id": "page-1",
                "object": "page",
                "created_time": "2025-01-01T00:00:00.000Z",
                "last_edited_time": "2025-01-02T00:00:00.000Z",
                "url": "https://notion.so/page-1",
                "properties": {
                    "title": {"title": [{"plain_text": "Product Requirements Doc"}]}
                },
            }
        ],
        "has_more": False,
    }

    async def fake_notion_api_request(method, endpoint, access_token, logger, **kwargs):
        assert method == "POST"
        assert endpoint == "/search"
        assert access_token == "secret-token"
        assert kwargs.get("json_payload", {}).get("query") == search_query
        return fake_notion_response

    monkeypatch.setattr(
        mcp_notion_proxy, "get_notion_credentials", fake_get_credentials
    )
    monkeypatch.setattr(
        mcp_notion_proxy,
        "ensure_fresh_notion_credentials",
        fake_ensure_fresh_credentials,
    )
    monkeypatch.setattr(
        mcp_notion_proxy, "_notion_api_request", fake_notion_api_request
    )

    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 2,
        "params": {
            "name": "notion_search",
            "arguments": {
                "query": search_query,
            },
        },
        "meta": {
            "user_id": "user-123",
            "space_id": space_id,
        },
    }

    response = api_client.post("/mcp/notion/proxy", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "content" in data["result"]
    assert data["result"]["isError"] is False
    assert "_meta" in data["result"]
    assert len(data["result"]["_meta"]["results"]) == 1
    assert data["result"]["_meta"]["results"][0]["title"] == "Product Requirements Doc"


def test_mcp_notion_proxy_get_page_tool(api_client: TestClient, monkeypatch):
    """Test that notion_get_page tool retrieves a page."""
    space_id = "space-with-notion"
    page_id = "test-page-123"

    credentials = NotionCredentials(
        access_token="secret-token",
        refresh_token=None,
        token_expires_at=None,
        workspace_id="workspace-123",
        workspace_name="Acme Workspace",
        bot_id="bot-id",
        process_id="process-secret",
        auth_mode="oauth",
    )

    async def fake_get_credentials(event_store, requested_space_id):
        return credentials

    async def fake_ensure_fresh_credentials(**_kwargs):
        return credentials

    fake_page_data = {
        "id": page_id,
        "object": "page",
        "properties": {"title": {"title": [{"plain_text": "Test Page"}]}},
    }

    async def fake_notion_api_request(method, endpoint, access_token, logger, **kwargs):
        assert method == "GET"
        assert endpoint == f"/pages/{page_id}"
        return fake_page_data

    monkeypatch.setattr(
        mcp_notion_proxy, "get_notion_credentials", fake_get_credentials
    )
    monkeypatch.setattr(
        mcp_notion_proxy,
        "ensure_fresh_notion_credentials",
        fake_ensure_fresh_credentials,
    )
    monkeypatch.setattr(
        mcp_notion_proxy, "_notion_api_request", fake_notion_api_request
    )

    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 3,
        "params": {
            "name": "notion_get_page",
            "arguments": {
                "page_id": page_id,
            },
        },
        "meta": {
            "user_id": "user-123",
            "space_id": space_id,
        },
    }

    response = api_client.post("/mcp/notion/proxy", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert data["result"]["isError"] is False
    assert data["result"]["_meta"]["id"] == page_id


def test_mcp_notion_proxy_get_block_children_tool(api_client: TestClient, monkeypatch):
    """Test that notion_get_block_children tool retrieves block content."""
    space_id = "space-with-notion"
    block_id = "test-block-456"

    credentials = NotionCredentials(
        access_token="secret-token",
        refresh_token=None,
        token_expires_at=None,
        workspace_id="workspace-123",
        workspace_name="Acme Workspace",
        bot_id="bot-id",
        process_id="process-secret",
        auth_mode="oauth",
    )

    async def fake_get_credentials(event_store, requested_space_id):
        return credentials

    async def fake_ensure_fresh_credentials(**_kwargs):
        return credentials

    fake_blocks_data = {
        "results": [
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"plain_text": "This is a test paragraph."}]
                },
            },
            {
                "type": "heading_1",
                "heading_1": {"rich_text": [{"plain_text": "Test Heading"}]},
            },
        ],
        "has_more": False,
    }

    async def fake_notion_api_request(method, endpoint, access_token, logger, **kwargs):
        assert method == "GET"
        assert f"/blocks/{block_id}/children" in endpoint
        return fake_blocks_data

    monkeypatch.setattr(
        mcp_notion_proxy, "get_notion_credentials", fake_get_credentials
    )
    monkeypatch.setattr(
        mcp_notion_proxy,
        "ensure_fresh_notion_credentials",
        fake_ensure_fresh_credentials,
    )
    monkeypatch.setattr(
        mcp_notion_proxy, "_notion_api_request", fake_notion_api_request
    )

    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 4,
        "params": {
            "name": "notion_get_block_children",
            "arguments": {
                "block_id": block_id,
            },
        },
        "meta": {
            "user_id": "user-123",
            "space_id": space_id,
        },
    }

    response = api_client.post("/mcp/notion/proxy", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert data["result"]["isError"] is False
    assert "This is a test paragraph" in data["result"]["content"][0]["text"]
    assert "Test Heading" in data["result"]["content"][0]["text"]
    assert data["result"]["_meta"]["block_count"] == 2


def test_mcp_notion_proxy_list_databases_tool(api_client: TestClient, monkeypatch):
    """Test that notion_list_databases tool lists all databases."""
    space_id = "space-with-notion"

    credentials = NotionCredentials(
        access_token="secret-token",
        refresh_token=None,
        token_expires_at=None,
        workspace_id="workspace-123",
        workspace_name="Acme Workspace",
        bot_id="bot-id",
        process_id="process-secret",
        auth_mode="oauth",
    )

    async def fake_get_credentials(event_store, requested_space_id):
        return credentials

    async def fake_ensure_fresh_credentials(**_kwargs):
        return credentials

    fake_search_data = {
        "results": [
            {
                "object": "database",
                "id": "db-123",
                "title": [{"plain_text": "Projects"}],
                "url": "https://notion.so/db-123",
                "created_time": "2024-01-01T00:00:00Z",
                "last_edited_time": "2024-01-02T00:00:00Z",
            },
            {
                "object": "database",
                "id": "db-456",
                "title": [{"plain_text": "Tasks"}],
                "url": "https://notion.so/db-456",
                "created_time": "2024-01-01T00:00:00Z",
                "last_edited_time": "2024-01-02T00:00:00Z",
            },
        ],
        "has_more": False,
    }

    async def fake_notion_api_request(method, endpoint, access_token, logger, **kwargs):
        assert method == "POST"
        assert endpoint == "/search"
        return fake_search_data

    monkeypatch.setattr(
        mcp_notion_proxy, "get_notion_credentials", fake_get_credentials
    )
    monkeypatch.setattr(
        mcp_notion_proxy,
        "ensure_fresh_notion_credentials",
        fake_ensure_fresh_credentials,
    )
    monkeypatch.setattr(
        mcp_notion_proxy, "_notion_api_request", fake_notion_api_request
    )

    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 5,
        "params": {
            "name": "notion_list_databases",
            "arguments": {},
        },
        "meta": {
            "user_id": "user-123",
            "space_id": space_id,
        },
    }

    response = api_client.post("/mcp/notion/proxy", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert data["result"]["isError"] is False
    assert data["result"]["content"][0]["text"] == "Found 2 databases"
    assert len(data["result"]["_meta"]["databases"]) == 2
    assert data["result"]["_meta"]["databases"][0]["title"] == "Projects"
    assert data["result"]["_meta"]["databases"][1]["title"] == "Tasks"


def test_mcp_notion_proxy_get_database_tool(api_client: TestClient, monkeypatch):
    """Test that notion_get_database tool retrieves database schema."""
    space_id = "space-with-notion"
    database_id = "db-123"

    credentials = NotionCredentials(
        access_token="secret-token",
        refresh_token=None,
        token_expires_at=None,
        workspace_id="workspace-123",
        workspace_name="Acme Workspace",
        bot_id="bot-id",
        process_id="process-secret",
        auth_mode="oauth",
    )

    async def fake_get_credentials(event_store, requested_space_id):
        return credentials

    async def fake_ensure_fresh_credentials(**_kwargs):
        return credentials

    fake_database_data = {
        "id": database_id,
        "title": [{"plain_text": "Projects"}],
        "url": "https://notion.so/db-123",
        "created_time": "2024-01-01T00:00:00Z",
        "last_edited_time": "2024-01-02T00:00:00Z",
        "properties": {
            "Name": {"type": "title", "id": "title"},
            "Status": {"type": "select", "id": "status"},
            "Due Date": {"type": "date", "id": "date"},
        },
    }

    async def fake_notion_api_request(method, endpoint, access_token, logger, **kwargs):
        assert method == "GET"
        assert endpoint == f"/databases/{database_id}"
        return fake_database_data

    monkeypatch.setattr(
        mcp_notion_proxy, "get_notion_credentials", fake_get_credentials
    )
    monkeypatch.setattr(
        mcp_notion_proxy,
        "ensure_fresh_notion_credentials",
        fake_ensure_fresh_credentials,
    )
    monkeypatch.setattr(
        mcp_notion_proxy, "_notion_api_request", fake_notion_api_request
    )

    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 6,
        "params": {
            "name": "notion_get_database",
            "arguments": {
                "database_id": database_id,
            },
        },
        "meta": {
            "user_id": "user-123",
            "space_id": space_id,
        },
    }

    response = api_client.post("/mcp/notion/proxy", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert data["result"]["isError"] is False
    assert "Database: Projects" in data["result"]["content"][0]["text"]
    assert data["result"]["_meta"]["title"] == "Projects"
    assert len(data["result"]["_meta"]["properties"]) == 3
    assert data["result"]["_meta"]["properties"]["Name"]["type"] == "title"


def test_mcp_notion_proxy_query_database_tool(api_client: TestClient, monkeypatch):
    """Test that notion_query_database tool queries a database with filters."""
    space_id = "space-with-notion"
    database_id = "db-123"

    credentials = NotionCredentials(
        access_token="secret-token",
        refresh_token=None,
        token_expires_at=None,
        workspace_id="workspace-123",
        workspace_name="Acme Workspace",
        bot_id="bot-id",
        process_id="process-secret",
        auth_mode="oauth",
    )

    async def fake_get_credentials(event_store, requested_space_id):
        return credentials

    async def fake_ensure_fresh_credentials(**_kwargs):
        return credentials

    fake_query_data = {
        "results": [
            {
                "id": "page-1",
                "url": "https://notion.so/page-1",
                "created_time": "2024-01-01T00:00:00Z",
                "last_edited_time": "2024-01-02T00:00:00Z",
                "properties": {
                    "Name": {
                        "type": "title",
                        "title": [{"plain_text": "Project Alpha"}],
                    },
                    "Status": {
                        "type": "select",
                        "select": {"name": "In Progress"},
                    },
                },
            },
            {
                "id": "page-2",
                "url": "https://notion.so/page-2",
                "created_time": "2024-01-01T00:00:00Z",
                "last_edited_time": "2024-01-02T00:00:00Z",
                "properties": {
                    "Name": {
                        "type": "title",
                        "title": [{"plain_text": "Project Beta"}],
                    },
                    "Status": {
                        "type": "select",
                        "select": {"name": "Complete"},
                    },
                },
            },
        ],
        "has_more": False,
    }

    async def fake_notion_api_request(method, endpoint, access_token, logger, **kwargs):
        assert method == "POST"
        assert endpoint == f"/databases/{database_id}/query"
        return fake_query_data

    monkeypatch.setattr(
        mcp_notion_proxy, "get_notion_credentials", fake_get_credentials
    )
    monkeypatch.setattr(
        mcp_notion_proxy,
        "ensure_fresh_notion_credentials",
        fake_ensure_fresh_credentials,
    )
    monkeypatch.setattr(
        mcp_notion_proxy, "_notion_api_request", fake_notion_api_request
    )

    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": 7,
        "params": {
            "name": "notion_query_database",
            "arguments": {
                "database_id": database_id,
                "filter": {"property": "Status", "select": {"equals": "In Progress"}},
            },
        },
        "meta": {
            "user_id": "user-123",
            "space_id": space_id,
        },
    }

    response = api_client.post("/mcp/notion/proxy", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert data["result"]["isError"] is False
    assert data["result"]["content"][0]["text"] == "Found 2 entries"
    assert len(data["result"]["_meta"]["results"]) == 2
    assert (
        data["result"]["_meta"]["results"][0]["properties"]["Name"]["value"]
        == "Project Alpha"
    )
    assert (
        data["result"]["_meta"]["results"][0]["properties"]["Status"]["value"]
        == "In Progress"
    )
