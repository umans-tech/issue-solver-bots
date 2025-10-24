"""Tests for Notion MCP proxy functionality."""

from datetime import datetime, UTC, timedelta

import pytest
from starlette.testclient import TestClient

from issue_solver.webapi.routers import notion_integration, mcp_notion_proxy
from issue_solver.events.notion_integration import NotionCredentials


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


def test_mcp_notion_proxy_missing_space_id(api_client: TestClient):
    payload = {
        "meta": {
            "user_id": "user-123",
        },
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1,
    }

    response = api_client.post("/mcp/notion/proxy", json=payload)

    assert response.status_code == 400
    assert "Missing space_id" in response.json()["detail"]


def test_mcp_notion_proxy_no_integration(api_client: TestClient):
    payload = {
        "meta": {"user_id": "user-123", "space_id": "space-without-notion"},
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1,
    }

    response = api_client.post("/mcp/notion/proxy", json=payload)

    assert response.status_code == 404
    assert "No Notion integration connected" in response.json()["detail"]


def test_mcp_notion_proxy_forwards_request(api_client: TestClient, monkeypatch):
    space_id = "space-with-notion"
    user_id = "user-123"

    captured: dict[str, object | None] = {}

    credentials = NotionCredentials(
        access_token="secret",
        refresh_token="refresh-secret",
        token_expires_at=datetime.now(UTC) + timedelta(hours=1),
        workspace_id="workspace-123",
        workspace_name="Acme Workspace",
        bot_id="bot-id",
        process_id="process-secret",
        auth_mode="oauth",
    )

    monkeypatch.setenv("NOTION_MCP_CLIENT_ID", "stub-mcp-client-id")
    monkeypatch.setenv("NOTION_MCP_CLIENT_SECRET", "stub-mcp-client-secret")

    async def fake_get_credentials(event_store, requested_space_id):
        assert requested_space_id == space_id
        return credentials

    async def fake_ensure_fresh_credentials(**_kwargs):
        return credentials

    async def fake_forward(
        endpoint: str,
        token: str,
        payload: dict,
        session_id: str | None,
    ):
        captured["endpoint"] = endpoint
        captured["token"] = token
        captured["payload"] = payload
        captured["session"] = session_id
        return {"status": "ok"}, session_id or "session-generated"

    monkeypatch.setattr(
        mcp_notion_proxy, "get_notion_credentials", fake_get_credentials
    )
    monkeypatch.setattr(
        mcp_notion_proxy,
        "ensure_fresh_notion_credentials",
        fake_ensure_fresh_credentials,
    )

    async def fake_get_mcp_token(*, credentials, logger):
        assert credentials.access_token == "secret"
        return "mcp-secret-token"

    monkeypatch.setattr(
        mcp_notion_proxy,
        "get_mcp_access_token",
        fake_get_mcp_token,
    )
    monkeypatch.setattr(mcp_notion_proxy, "_forward_to_notion", fake_forward)

    response = api_client.post(
        "/mcp/notion/proxy",
        json={"meta": {"user_id": user_id, "space_id": space_id}},
        headers={"mcp-session-id": "session-1"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["mcp-session-id"] == "session-1"
    endpoint = captured["endpoint"]
    assert isinstance(endpoint, str)
    assert endpoint == mcp_notion_proxy.NOTION_MCP_REMOTE_ENDPOINT
    assert captured["token"] == "mcp-secret-token"
    assert isinstance(captured["payload"], dict)
    assert captured["session"] == "session-1"
