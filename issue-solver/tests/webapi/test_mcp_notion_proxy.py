"""Tests for Notion MCP proxy functionality."""

from datetime import datetime, UTC, timedelta

import httpx
import pytest
from fastapi import HTTPException
from starlette.testclient import TestClient

from issue_solver.webapi.routers import notion_integration, mcp_notion_proxy
from issue_solver.events.notion_integration import NotionCredentials


@pytest.fixture(autouse=True)
def stub_oauth_config(monkeypatch):
    notion_integration._get_mcp_settings.cache_clear()
    monkeypatch.setenv("NOTION_MCP_CLIENT_ID", "stub-mcp-client-id")
    monkeypatch.setenv("NOTION_MCP_CLIENT_SECRET", "stub-mcp-client-secret")
    monkeypatch.setenv(
        "NOTION_MCP_OAUTH_REDIRECT_URI",
        "https://example.com/notion/mcp/callback",
    )
    monkeypatch.setenv("NOTION_MCP_RETURN_BASE_URL", "https://frontend.example.com")
    yield
    notion_integration._get_mcp_settings.cache_clear()


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
        mcp_access_token=None,
        mcp_refresh_token="mcp-refresh-secret",
        mcp_token_expires_at=None,
        workspace_id="workspace-123",
        workspace_name="Acme Workspace",
        bot_id="bot-id",
        process_id="process-secret",
    )

    monkeypatch.setenv("NOTION_MCP_CLIENT_ID", "stub-mcp-client-id")
    monkeypatch.setenv("NOTION_MCP_CLIENT_SECRET", "stub-mcp-client-secret")

    async def fake_get_credentials(event_store, requested_space_id):
        assert requested_space_id == space_id
        return credentials

    async def fake_ensure_fresh_credentials(**_kwargs):
        return NotionCredentials(
            mcp_access_token="mcp-secret-token",
            mcp_refresh_token=credentials.mcp_refresh_token,
            mcp_token_expires_at=datetime.now(UTC) + timedelta(hours=1),
            workspace_id=credentials.workspace_id,
            workspace_name=credentials.workspace_name,
            bot_id=credentials.bot_id,
            process_id=credentials.process_id,
        )

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
        next_session = session_id or "session-generated"
        response = httpx.Response(
            status_code=200,
            json={"status": "ok"},
            headers={
                "mcp-session-id": next_session,
                "content-type": "application/json",
            },
        )
        return response, next_session

    monkeypatch.setattr(
        mcp_notion_proxy, "get_notion_credentials", fake_get_credentials
    )
    monkeypatch.setattr(
        mcp_notion_proxy,
        "ensure_fresh_notion_credentials",
        fake_ensure_fresh_credentials,
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


def test_mcp_notion_proxy_handles_invalid_grant_error(
    api_client: TestClient, monkeypatch
):
    space_id = "space-mismatch"

    credentials = NotionCredentials(
        mcp_access_token=None,
        mcp_refresh_token="mcp-refresh-secret",
        mcp_token_expires_at=None,
        workspace_id="workspace-123",
        workspace_name="Acme Workspace",
        bot_id="bot-id",
        process_id="process-secret",
    )

    async def fake_get_credentials(event_store, requested_space_id):
        assert requested_space_id == space_id
        return credentials

    called: dict[str, bool] = {}

    async def fake_ensure_fresh_credentials(**_kwargs):
        called["ensure"] = True
        raise HTTPException(
            status_code=401, detail=mcp_notion_proxy.MCP_RECONNECT_MESSAGE
        )

    monkeypatch.setattr(
        mcp_notion_proxy, "get_notion_credentials", fake_get_credentials
    )
    monkeypatch.setattr(
        mcp_notion_proxy,
        "ensure_fresh_notion_credentials",
        fake_ensure_fresh_credentials,
    )

    response = api_client.post(
        "/mcp/notion/proxy",
        json={"meta": {"user_id": "user-123", "space_id": space_id}},
    )

    assert response.status_code == 401
    assert mcp_notion_proxy.MCP_RECONNECT_MESSAGE in response.json()["detail"]
    assert called.get("ensure") is True
