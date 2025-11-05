from __future__ import annotations

import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from pytest_httpserver import HTTPServer
from werkzeug.wrappers import Response

from issue_solver.events.domain import (
    NotionIntegrationAuthorized,
    NotionIntegrationAuthorizationFailed,
    NotionIntegrationTokenRefreshed,
)
from issue_solver.webapi.routers import mcp_notion_proxy, notion_integration
from issue_solver.webapi.routers.notion_integration import (
    MCP_OAUTH_STATE_CACHE_PREFIX,
    MCP_RECONNECT_MESSAGE,
)

DEFAULT_MCP_ENV = {
    "NOTION_MCP_CLIENT_ID": "component-test-client-id",
    "NOTION_MCP_CLIENT_SECRET": "component-test-client-secret",
    "NOTION_MCP_OAUTH_REDIRECT_URI": "https://api.issue-solver.dev/integrations/notion/mcp/callback",
    "NOTION_MCP_AUTHORIZE_ENDPOINT": "https://mcp.notion.com/authorize",
    "NOTION_MCP_TOKEN_ENDPOINT": "https://mcp.notion.com/token",
    "NOTION_MCP_RETURN_BASE_URL": "https://frontend.issue-solver.dev",
    "NOTION_MCP_STATE_TTL_SECONDS": "600",
}


def require_redirect_refresh_handler(expected_redirect_uri: str):
    def handler(request):
        form_data = parse_qs(request.get_data(as_text=True))
        redirect_values = form_data.get("redirect_uri", [])
        if redirect_values != [expected_redirect_uri]:
            failure_body = json.dumps(
                {
                    "error": "invalid_grant",
                    "error_description": "Grant not found",
                }
            )
            return Response(
                response=failure_body,
                status=400,
                content_type="application/json",
            )
        success_body = json.dumps(
            {
                "access_token": "mcp-access-refreshed",
                "refresh_token": "mcp-refresh-refreshed",
                "expires_in": 3600,
                "workspace_id": "workspace-refresh",
                "workspace_name": "Workspace After Refresh",
                "bot_id": "bot-refresh",
            }
        )
        return Response(
            response=success_body,
            status=200,
            content_type="application/json",
        )

    return handler


@contextmanager
def configured_mcp_env(**overrides: str) -> Iterator[None]:
    keys = set(DEFAULT_MCP_ENV) | set(overrides)
    previous = {key: os.environ.get(key) for key in keys}
    try:
        for key in keys:
            value = overrides.get(key, DEFAULT_MCP_ENV.get(key))
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        notion_integration._get_mcp_settings.cache_clear()
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        notion_integration._get_mcp_settings.cache_clear()


def test_get_notion_integration_returns_404_when_space_is_unknown(api_client) -> None:
    # When
    response = api_client.get("/integrations/notion/space-not-found")

    # Then
    assert response.status_code == 404
    assert response.json()["detail"].startswith("No Notion integration configured")


def test_get_notion_integration_returns_latest_mcp_snapshot(api_client) -> None:
    # Given
    space_id = "space-northwind"
    process_id = "process-northwind"
    connected_at = datetime(2025, 10, 30, 11, 0)
    rotation_at = connected_at + timedelta(minutes=7)

    connected = NotionIntegrationAuthorized(
        occurred_at=connected_at,
        user_id="user-123",
        space_id=space_id,
        process_id=process_id,
        workspace_id="workspace-initial",
        workspace_name="Northwind Starter",
        bot_id="bot-initial",
        mcp_access_token="token-initial",
        mcp_refresh_token="refresh-initial",
        mcp_token_expires_at=connected_at + timedelta(hours=1),
    )

    rotation = NotionIntegrationTokenRefreshed(
        occurred_at=rotation_at,
        user_id="user-456",
        space_id=space_id,
        process_id=process_id,
        workspace_id="workspace-latest",
        workspace_name="Northwind HQ",
        bot_id="bot-latest",
        mcp_access_token="token-latest",
        mcp_refresh_token="refresh-latest",
        mcp_token_expires_at=rotation_at + timedelta(hours=2),
    )

    event_store = api_client.app.state.event_store
    api_client.portal.call(event_store.append, process_id, connected, rotation)

    # When
    response = api_client.get(f"/integrations/notion/{space_id}")

    # Then
    assert response.status_code == 200
    body = response.json()
    assert body["spaceId"] == space_id
    assert body["processId"] == process_id
    assert body["workspaceId"] == "workspace-latest"
    assert body["workspaceName"] == "Northwind HQ"
    assert body["botId"] == "bot-latest"
    assert body["connectedAt"] == connected_at.isoformat()
    assert body["hasMcpToken"] is True


def test_start_notion_mcp_oauth_flow_persists_state(api_client, redis_client) -> None:
    # Given
    space_id = "space-oauth-start"
    user_id = "user-oauth-start"
    return_path = "/integrations/notion/return"

    with configured_mcp_env():
        # When
        response = api_client.get(
            "/integrations/notion/oauth/mcp/start",
            params={"space_id": space_id, "return_path": return_path},
            headers={"X-User-ID": user_id},
        )

        # Then
        assert response.status_code == 200
        payload = response.json()
        state = payload["state"]
        authorize_url = payload["authorizeUrl"]

        parsed = urlparse(authorize_url)
        assert parsed.scheme == "https"
        assert parsed.netloc == "mcp.notion.com"
        query = parse_qs(parsed.query)
        assert query["client_id"] == [DEFAULT_MCP_ENV["NOTION_MCP_CLIENT_ID"]]
        assert query["redirect_uri"] == [
            DEFAULT_MCP_ENV["NOTION_MCP_OAUTH_REDIRECT_URI"]
        ]
        assert query["state"] == [state]

        cached_state = redis_client.get(f"{MCP_OAUTH_STATE_CACHE_PREFIX}{state}")
        assert cached_state is not None
        decoded = json.loads(cached_state)
        assert decoded == {
            "space_id": space_id,
            "user_id": user_id,
            "return_path": return_path,
        }


def test_handle_notion_mcp_oauth_callback_creates_connected_integration(
    api_client,
    time_under_control,
    httpserver: HTTPServer,
) -> None:
    # Given
    time_under_control.set_from_iso_format("2025-10-31T10:05:00")
    space_id = "space-oauth-complete"
    user_id = "user-oauth-complete"

    token_endpoint = httpserver.url_for("/oauth/token")
    httpserver.expect_request(
        "/oauth/token",
        method="POST",
    ).respond_with_json(
        {
            "access_token": "mcp-access-connected",
            "refresh_token": "mcp-refresh-connected",
            "expires_in": 3600,
            "workspace_id": "workspace-connected",
            "workspace_name": "Workspace Connected",
            "bot_id": "bot-connected",
        },
        status=200,
    )

    with configured_mcp_env(NOTION_MCP_TOKEN_ENDPOINT=token_endpoint):
        start_response = api_client.get(
            "/integrations/notion/oauth/mcp/start",
            params={"space_id": space_id},
            headers={"X-User-ID": user_id},
        )
        state = start_response.json()["state"]

        # When
        callback_response = api_client.get(
            "/integrations/notion/mcp/oauth/callback",
            params={"code": "auth-code-123", "state": state},
            follow_redirects=False,
        )

    # Then
    assert callback_response.status_code == 303
    redirect_location = callback_response.headers["location"]
    parsed = urlparse(redirect_location)
    query = parse_qs(parsed.query)
    assert query["status"] == ["success"]
    assert query["spaceId"] == [space_id]
    assert query["mcp"] == ["connected"]
    assert "processId" in query

    integration_view = api_client.get(f"/integrations/notion/{space_id}").json()
    assert integration_view["hasMcpToken"] is True
    assert integration_view["workspaceId"] == "workspace-connected"
    process_id = integration_view["processId"]

    event_store = api_client.app.state.event_store
    events = api_client.portal.call(event_store.get, process_id)
    connected = next(
        event for event in events if isinstance(event, NotionIntegrationAuthorized)
    )
    assert connected.mcp_access_token == "mcp-access-connected"
    assert connected.mcp_refresh_token == "mcp-refresh-connected"
    assert connected.workspace_id == "workspace-connected"
    assert connected.user_id == user_id


def test_handle_notion_mcp_oauth_callback_returns_400_without_state(
    api_client,
) -> None:
    # Given
    with configured_mcp_env():
        # When
        response = api_client.get(
            "/integrations/notion/mcp/oauth/callback",
            params={"code": "missing-state"},
        )

        # Then
        assert response.status_code == 400
        assert response.json()["detail"] == "Missing OAuth state parameter."


def test_notion_mcp_proxy_returns_400_when_space_is_missing(api_client) -> None:
    # When
    response = api_client.post(
        "/mcp/notion/proxy",
        json={
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1,
            "meta": {"user_id": "user-123"},
        },
    )

    # Then
    assert response.status_code == 400
    assert "Missing space_id" in response.json()["detail"]


def test_notion_mcp_proxy_returns_404_when_integration_is_missing(api_client) -> None:
    # When
    response = api_client.post(
        "/mcp/notion/proxy",
        json={
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1,
            "meta": {"user_id": "user-123", "space_id": "space-without-notion"},
        },
    )

    # Then
    assert response.status_code == 404
    assert "No Notion integration connected" in response.json()["detail"]


def test_notion_mcp_proxy_forwards_request_and_returns_remote_payload(
    api_client,
    time_under_control,
    httpserver: HTTPServer,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    time_under_control.set_from_iso_format("2025-10-31T12:00:00")
    space_id = "space-with-notion"
    process_id = "process-with-notion"

    event_store = api_client.app.state.event_store
    api_client.portal.call(
        event_store.append,
        process_id,
        NotionIntegrationAuthorized(
            occurred_at=time_under_control.now(),
            user_id="user-123",
            space_id=space_id,
            process_id=process_id,
            workspace_id="workspace-ready",
            workspace_name="Workspace Ready",
            bot_id="bot-ready",
            mcp_access_token="mcp-valid-token",
            mcp_refresh_token="mcp-refresh-token",
            mcp_token_expires_at=time_under_control.now() + timedelta(hours=1),
        ),
    )

    remote_endpoint = httpserver.url_for("/mcp")
    httpserver.expect_request(
        "/mcp",
        method="POST",
        json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
        headers={
            "Authorization": "Bearer mcp-valid-token",
            "mcp-session-id": "session-in",
        },
    ).respond_with_json(
        {"jsonrpc": "2.0", "result": {"status": "ok"}},
        headers={"mcp-session-id": "session-out"},
    )

    monkeypatch.setattr(
        mcp_notion_proxy,
        "NOTION_MCP_REMOTE_ENDPOINT",
        remote_endpoint,
    )

    # When
    response = api_client.post(
        "/mcp/notion/proxy",
        json={
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1,
            "meta": {"user_id": "user-123", "space_id": space_id},
        },
        headers={"mcp-session-id": "session-in"},
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {"jsonrpc": "2.0", "result": {"status": "ok"}}
    assert response.headers["mcp-session-id"] == "session-out"


def test_notion_mcp_proxy_refreshes_expired_token_when_redirect_uri_provided(
    api_client,
    time_under_control,
    httpserver: HTTPServer,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    time_under_control.set_from_iso_format("2025-10-31T13:05:00")
    space_id = "space-token-refresh"
    process_id = "process-token-refresh"
    event_store = api_client.app.state.event_store
    connected_at = time_under_control.now() - timedelta(hours=1)
    expired_at = time_under_control.now() - timedelta(minutes=1)

    api_client.portal.call(
        event_store.append,
        process_id,
        NotionIntegrationAuthorized(
            occurred_at=connected_at,
            user_id="user-refresh",
            space_id=space_id,
            process_id=process_id,
            workspace_id="workspace-before-refresh",
            workspace_name="Workspace Before Refresh",
            bot_id="bot-before-refresh",
            mcp_access_token="mcp-expired-token",
            mcp_refresh_token="mcp-refresh-token",
            mcp_token_expires_at=expired_at,
        ),
    )

    token_endpoint = httpserver.url_for("/oauth/token")
    remote_endpoint = httpserver.url_for("/mcp")

    with configured_mcp_env(NOTION_MCP_TOKEN_ENDPOINT=token_endpoint):
        expected_redirect = os.environ["NOTION_MCP_OAUTH_REDIRECT_URI"]
        httpserver.expect_request(
            "/oauth/token",
            method="POST",
        ).respond_with_handler(require_redirect_refresh_handler(expected_redirect))

        httpserver.expect_request(
            "/mcp",
            method="POST",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            headers={
                "Authorization": "Bearer mcp-access-refreshed",
                "mcp-session-id": "session-in",
            },
        ).respond_with_json(
            {"jsonrpc": "2.0", "result": {"status": "refreshed"}},
            headers={"mcp-session-id": "session-out"},
        )

        monkeypatch.setattr(
            mcp_notion_proxy,
            "NOTION_MCP_REMOTE_ENDPOINT",
            remote_endpoint,
        )

        # When
        response = api_client.post(
            "/mcp/notion/proxy",
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1,
                "meta": {"user_id": "user-refresh", "space_id": space_id},
            },
            headers={"mcp-session-id": "session-in"},
        )

    # Then
    assert response.status_code == 200
    assert response.json() == {"jsonrpc": "2.0", "result": {"status": "refreshed"}}
    assert response.headers["mcp-session-id"] == "session-out"

    events = api_client.portal.call(event_store.get, process_id)
    rotation = next(
        event for event in events if isinstance(event, NotionIntegrationTokenRefreshed)
    )
    assert rotation.mcp_access_token == "mcp-access-refreshed"
    assert rotation.mcp_refresh_token == "mcp-refresh-refreshed"
    assert rotation.workspace_name == "Workspace After Refresh"


def test_notion_mcp_proxy_returns_401_when_refresh_fails_with_invalid_grant(
    api_client,
    time_under_control,
    httpserver: HTTPServer,
) -> None:
    # Given
    time_under_control.set_from_iso_format("2025-10-31T13:15:00")
    space_id = "space-token-refresh"
    process_id = "process-token-refresh"
    event_store = api_client.app.state.event_store

    api_client.portal.call(
        event_store.append,
        process_id,
        NotionIntegrationAuthorized(
            occurred_at=time_under_control.now(),
            user_id="user-refresh",
            space_id=space_id,
            process_id=process_id,
            workspace_id="workspace-refresh",
            workspace_name="Workspace Refresh",
            bot_id="bot-refresh",
            mcp_access_token="mcp-expired-token",
            mcp_refresh_token="mcp-refresh-token",
            mcp_token_expires_at=time_under_control.now(),
        ),
    )

    token_endpoint = httpserver.url_for("/oauth/token")
    httpserver.expect_request(
        "/oauth/token",
        method="POST",
    ).respond_with_json({"error": "invalid_grant"}, status=400)

    with configured_mcp_env(NOTION_MCP_TOKEN_ENDPOINT=token_endpoint):
        # When
        response = api_client.post(
            "/mcp/notion/proxy",
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1,
                "meta": {"user_id": "user-refresh", "space_id": space_id},
            },
        )

    # Then
    assert response.status_code == 401
    assert response.json()["detail"] == MCP_RECONNECT_MESSAGE

    events = api_client.portal.call(event_store.get, process_id)
    failure = next(
        event
        for event in events
        if isinstance(event, NotionIntegrationAuthorizationFailed)
    )
    assert failure.error_type == "invalid_grant"
