from contextlib import contextmanager
from datetime import datetime, UTC

import pytest
from starlette.testclient import TestClient

from issue_solver.webapi.routers import notion_integration, mcp_notion_proxy
from issue_solver.webapi.main import app
from issue_solver.webapi.dependencies import get_event_store, get_clock
from issue_solver.events.event_store import InMemoryEventStore
from issue_solver.clock import Clock


class _FrozenClock(Clock):
    def __init__(self, moment: datetime | None = None) -> None:
        self._moment = moment or datetime(2025, 1, 1, tzinfo=UTC)

    def now(self) -> datetime:
        return self._moment


@contextmanager
def notion_test_client(event_store: InMemoryEventStore, clock: Clock):
    overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_event_store] = lambda: event_store
    app.dependency_overrides[get_clock] = lambda: clock
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides = overrides


@pytest.fixture(autouse=True)
def stub_notion_validation(monkeypatch):
    async def fake_validate(access_token: str) -> dict:
        return {
            "object": "user",
            "id": "bot-id",
            "name": "Automation Bot",
            "bot": {
                "workspace_id": "workspace-123",
                "workspace_name": "Acme Workspace",
            },
            "token_used": access_token,
        }

    monkeypatch.setattr(notion_integration, "_validate_notion_token", fake_validate)
    yield
    monkeypatch.delattr(notion_integration, "_validate_notion_token")


def test_connect_notion_integration_success(api_client):
    space_id = "space-123"
    user_id = "user-42"

    response = api_client.post(
        "/integrations/notion/",
        json={"access_token": "secret-token", "space_id": space_id},
        headers={"X-User-ID": user_id},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["spaceId"] == space_id
    assert data["workspaceName"] == "Acme Workspace"
    assert data["botId"] == "bot-id"
    assert "processId" in data
    assert data.get("tokenExpiresAt") is None

    fetch_response = api_client.get(f"/integrations/notion/{space_id}")
    assert fetch_response.status_code == 200
    fetched = fetch_response.json()
    assert fetched["spaceId"] == space_id
    assert fetched["workspaceId"] == "workspace-123"
    assert fetched["hasValidToken"] is True
    assert fetched.get("tokenExpiresAt") is None


def test_get_notion_integration_returns_404_when_missing(api_client):
    response = api_client.get("/integrations/notion/unknown-space")
    assert response.status_code == 404


def test_rotate_notion_token(monkeypatch):
    space_id = "space-rotate"
    user_id = "user-rotate"

    async def validate_new_token(access_token: str) -> dict:
        if access_token == "initial-token":
            return {
                "object": "user",
                "id": "bot-id",
                "bot": {
                    "workspace_id": "workspace-123",
                    "workspace_name": "Acme Workspace",
                },
            }
        assert access_token == "new-token"
        return {
            "object": "user",
            "id": "bot-id",
            "bot": {
                "workspace_id": "workspace-123",
                "workspace_name": "Acme Workspace",
            },
        }

    monkeypatch.setattr(
        notion_integration, "_validate_notion_token", validate_new_token
    )

    with notion_test_client(InMemoryEventStore(), _FrozenClock()) as client:
        client.post(
            "/integrations/notion/",
            json={"access_token": "initial-token", "space_id": space_id},
            headers={"X-User-ID": user_id},
        )

        rotate_resp = client.put(
            f"/integrations/notion/{space_id}/token",
            json={"access_token": "new-token"},
            headers={"X-User-ID": user_id},
        )

    assert rotate_resp.status_code == 200
    payload = rotate_resp.json()
    assert payload["spaceId"] == space_id
    assert payload["hasValidToken"] is True
    assert payload.get("tokenExpiresAt") is None


def test_notion_mcp_proxy_requires_integration(api_client):
    response = api_client.post(
        "/mcp/notion/proxy",
        json={"meta": {"space_id": "no-space", "user_id": "user"}},
    )
    assert response.status_code == 404


def test_notion_mcp_proxy_forwards_requests(api_client, monkeypatch):
    space_id = "space-proxy"
    user_id = "user-proxy"

    api_client.post(
        "/integrations/notion/",
        json={"access_token": "proxy-token", "space_id": space_id},
        headers={"X-User-ID": user_id},
    )

    captured: dict[str, object | None] = {}

    async def fake_forward(
        endpoint: str,
        access_token: str,
        payload: dict,
        session_id: str | None,
    ):
        captured["endpoint"] = endpoint
        captured["token"] = access_token
        captured["payload"] = payload
        captured["session"] = session_id
        return {"status": "ok", "tool": "list_pages"}, session_id or "generated-session"

    monkeypatch.setattr(mcp_notion_proxy, "_forward_to_notion", fake_forward)

    response = api_client.post(
        "/mcp/notion/proxy",
        json={"meta": {"space_id": space_id, "user_id": user_id}},
        headers={"mcp-session-id": "session-1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["tool"] == "list_pages"
    assert response.headers["mcp-session-id"] == "session-1"

    endpoint = captured["endpoint"]
    assert isinstance(endpoint, str)
    assert endpoint == mcp_notion_proxy.NOTION_MCP_REMOTE_ENDPOINT
    assert captured["token"] == "proxy-token"
    assert isinstance(captured["payload"], dict)
    assert captured["session"] == "session-1"


def test_notion_oauth_start_and_callback(monkeypatch):
    space_id = "space-oauth"
    user_id = "user-oauth"

    monkeypatch.setenv("NOTION_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setenv("NOTION_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv(
        "NOTION_OAUTH_REDIRECT_URI",
        "https://backend.test/integrations/notion/oauth/callback",
    )

    async def fake_request_oauth_token(*, payload, config, logger):
        grant_type = payload.get("grant_type")
        if grant_type == "authorization_code":
            return {
                "access_token": "oauth-access-token",
                "refresh_token": "oauth-refresh-token",
                "expires_in": 3600,
                "workspace_id": "workspace-oauth",
                "workspace_name": "OAuth Workspace",
                "bot_id": "bot-oauth",
            }
        if grant_type == "refresh_token":
            return {
                "access_token": "oauth-access-token-refreshed",
                "refresh_token": payload["refresh_token"],
                "expires_in": 3600,
            }
        raise AssertionError(f"Unexpected grant type: {grant_type}")

    monkeypatch.setattr(
        notion_integration,
        "_request_oauth_token",
        fake_request_oauth_token,
    )

    with notion_test_client(InMemoryEventStore(), _FrozenClock()) as client:
        start_resp = client.get(
            "/integrations/notion/oauth/start",
            params={"space_id": space_id},
            headers={"X-User-ID": user_id},
        )
        assert start_resp.status_code == 200
        start_data = start_resp.json()
        assert "authorizeUrl" in start_data
        assert "state" in start_data

        callback_resp = client.get(
            "/integrations/notion/oauth/callback",
            params={"code": "auth-code", "state": start_data["state"]},
            headers={"X-User-ID": user_id},
            follow_redirects=False,
        )
        assert callback_resp.status_code == 303
        assert callback_resp.headers["location"].startswith(
            "/integrations/notion/callback"
        )

        integration_resp = client.get(f"/integrations/notion/{space_id}")

    assert integration_resp.status_code == 200
    integration_data = integration_resp.json()
    assert integration_data["workspaceId"] == "workspace-oauth"
    assert integration_data["hasValidToken"] is True
    assert integration_data["tokenExpiresAt"] is not None
