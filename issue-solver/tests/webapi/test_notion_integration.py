from datetime import datetime, UTC, timedelta

import httpx
import pytest

from fastapi import HTTPException

from issue_solver.events.notion_integration import NotionCredentials
from issue_solver.webapi.routers import mcp_notion_proxy, notion_integration


@pytest.fixture(autouse=True)
def configure_mcp_env(monkeypatch):
    notion_integration._get_mcp_settings.cache_clear()
    monkeypatch.setenv("NOTION_MCP_CLIENT_ID", "stub-mcp-client-id")
    monkeypatch.setenv("NOTION_MCP_CLIENT_SECRET", "stub-mcp-client-secret")
    monkeypatch.setenv(
        "NOTION_MCP_OAUTH_REDIRECT_URI",
        "https://example.com/notion/mcp/callback",
    )
    monkeypatch.setenv("NOTION_MCP_STATE_TTL_SECONDS", "600")
    monkeypatch.setenv("NOTION_MCP_RETURN_BASE_URL", "https://frontend.example.com")
    yield
    notion_integration._get_mcp_settings.cache_clear()


def test_get_notion_integration_returns_404_when_missing(api_client):
    response = api_client.get("/integrations/notion/unknown-space")
    assert response.status_code == 404


def test_notion_mcp_oauth_flow(api_client, monkeypatch):
    space_id = "space-mcp"
    user_id = "user-mcp"

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
                "workspace_id": "workspace-mcp",
                "workspace_name": "MCP Workspace",
                "bot_id": "bot-mcp",
            }
        if endpoint == "https://mcp.notion.com/token" and grant_type == "refresh_token":
            return {
                "access_token": "mcp-access-token-refreshed",
                "refresh_token": payload["refresh_token"],
                "expires_in": 3600,
            }
        raise AssertionError(f"Unexpected grant type: {grant_type}")

    monkeypatch.setattr(
        notion_integration,
        "_request_oauth_token",
        fake_request_oauth_token,
    )

    start_resp = api_client.get(
        "/integrations/notion/oauth/mcp/start",
        params={"space_id": space_id},
        headers={"X-User-ID": user_id},
    )
    assert start_resp.status_code == 200
    start_state = start_resp.json()["state"]

    callback_resp = api_client.get(
        "/integrations/notion/mcp/oauth/callback",
        params={"code": "auth-code", "state": start_state},
        headers={"X-User-ID": user_id},
        follow_redirects=False,
    )
    assert callback_resp.status_code == 303
    final_location = callback_resp.headers["location"]
    assert final_location.startswith("https://frontend.example.com")

    integration_data = api_client.get(f"/integrations/notion/{space_id}").json()
    assert integration_data["spaceId"] == space_id
    assert integration_data["workspaceId"] == "workspace-mcp"
    assert integration_data["hasMcpToken"] is True
    assert integration_data["hasValidToken"] is False


def test_notion_mcp_flow_without_prior_integration(api_client, monkeypatch):
    space_id = "space-mcp-only"
    user_id = "user-mcp-only"

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
            }
        raise AssertionError(f"Unexpected exchange: {grant_type}")

    monkeypatch.setattr(
        notion_integration,
        "_request_oauth_token",
        fake_request_oauth_token,
    )

    start_resp = api_client.get(
        "/integrations/notion/oauth/mcp/start",
        params={"space_id": space_id},
        headers={"X-User-ID": user_id},
    )
    state = start_resp.json()["state"]

    api_client.get(  # no prior integration should exist
        "/integrations/notion/mcp/oauth/callback",
        params={"code": "mcp-code", "state": state},
        headers={"X-User-ID": user_id},
        follow_redirects=False,
    )

    integration_data = api_client.get(
        f"/integrations/notion/{space_id}",
        headers={"X-User-ID": user_id},
    ).json()
    assert integration_data["hasMcpToken"] is True
    assert integration_data["hasValidToken"] is False


def test_notion_mcp_proxy_requires_integration(api_client):
    response = api_client.post(
        "/mcp/notion/proxy",
        json={"meta": {"space_id": "no-space", "user_id": "user"}},
    )
    assert response.status_code == 404


def test_notion_mcp_proxy_forwards_request(api_client, monkeypatch):
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

    async def fake_get_credentials(event_store, requested_space_id):
        assert requested_space_id == space_id
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
        response = httpx.Response(
            status_code=200,
            json={"status": "ok"},
            headers={
                "mcp-session-id": session_id or "generated-session",
                "content-type": "application/json",
            },
        )
        return response, session_id or "generated-session"

    monkeypatch.setattr(
        mcp_notion_proxy, "get_notion_credentials", fake_get_credentials
    )

    async def fake_ensure(**_kwargs):
        return NotionCredentials(
            mcp_access_token="mcp-token",
            mcp_refresh_token=credentials.mcp_refresh_token,
            mcp_token_expires_at=datetime.now(UTC) + timedelta(hours=1),
            workspace_id=credentials.workspace_id,
            workspace_name=credentials.workspace_name,
            bot_id=credentials.bot_id,
            process_id=credentials.process_id,
        )

    monkeypatch.setattr(
        mcp_notion_proxy,
        "ensure_fresh_notion_credentials",
        fake_ensure,
    )

    monkeypatch.setattr(mcp_notion_proxy, "_forward_to_notion", fake_forward)

    response = api_client.post(
        "/mcp/notion/proxy",
        json={"meta": {"user_id": user_id, "space_id": space_id}},
        headers={"mcp-session-id": "session-1"},
    )

    assert response.status_code == 200
    assert captured["endpoint"] == mcp_notion_proxy.NOTION_MCP_REMOTE_ENDPOINT
    assert captured["token"] == "mcp-token"


def test_notion_mcp_proxy_handles_mcp_exchange_failure(api_client, monkeypatch):
    space_id = "space-mcp-fail"

    credentials = NotionCredentials(
        mcp_access_token=None,
        mcp_refresh_token="mcp-refresh-secret",
        mcp_token_expires_at=None,
        workspace_id="workspace-123",
        workspace_name="Acme Workspace",
        bot_id="bot-id",
        process_id="process-proxy",
    )

    async def fake_get_credentials(event_store, requested_space_id):
        assert requested_space_id == space_id
        return credentials

    async def fake_ensure(**_kwargs):
        raise HTTPException(status_code=503, detail="exchange failed")

    monkeypatch.setattr(
        mcp_notion_proxy, "get_notion_credentials", fake_get_credentials
    )
    monkeypatch.setattr(
        mcp_notion_proxy,
        "ensure_fresh_notion_credentials",
        fake_ensure,
    )

    response = api_client.post(
        "/mcp/notion/proxy",
        json={"meta": {"space_id": space_id, "user_id": "user"}},
        headers={"mcp-session-id": "session-1"},
    )

    assert response.status_code == 503
    assert "exchange failed" in response.json()["detail"]


def test_notion_mcp_proxy_rejects_credentials_without_mcp_token(
    api_client, monkeypatch
):
    space_id = "space-manual"

    async def fake_get_credentials(event_store, requested_space_id):
        assert requested_space_id == space_id
        return NotionCredentials(
            mcp_access_token=None,
            mcp_refresh_token=None,
            mcp_token_expires_at=None,
            workspace_id=None,
            workspace_name=None,
            bot_id=None,
            process_id="process-manual",
        )

    monkeypatch.setattr(
        mcp_notion_proxy, "get_notion_credentials", fake_get_credentials
    )

    response = api_client.post(
        "/mcp/notion/proxy",
        json={"meta": {"space_id": space_id, "user_id": "user"}},
        headers={"mcp-session-id": "session-legacy"},
    )

    assert response.status_code == 401
    assert mcp_notion_proxy.MCP_RECONNECT_MESSAGE in response.json()["detail"]
