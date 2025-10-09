import pytest

from issue_solver.webapi.routers import notion_integration, mcp_notion_proxy


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

    fetch_response = api_client.get(f"/integrations/notion/{space_id}")
    assert fetch_response.status_code == 200
    fetched = fetch_response.json()
    assert fetched["spaceId"] == space_id
    assert fetched["workspaceId"] == "workspace-123"
    assert fetched["hasValidToken"] is True


def test_get_notion_integration_returns_404_when_missing(api_client):
    response = api_client.get("/integrations/notion/unknown-space")
    assert response.status_code == 404


def test_rotate_notion_token(api_client, monkeypatch):
    space_id = "space-rotate"
    user_id = "user-rotate"

    api_client.post(
        "/integrations/notion/",
        json={"access_token": "initial-token", "space_id": space_id},
        headers={"X-User-ID": user_id},
    )

    async def validate_new_token(access_token: str) -> dict:
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

    rotate_resp = api_client.put(
        f"/integrations/notion/{space_id}/token",
        json={"access_token": "new-token"},
        headers={"X-User-ID": user_id},
    )
    assert rotate_resp.status_code == 200
    payload = rotate_resp.json()
    assert payload["spaceId"] == space_id
    assert payload["hasValidToken"] is True


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

    async def fake_forward(access_token: str, payload: dict, session_id: str | None):
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

    assert captured["token"] == "proxy-token"
    assert isinstance(captured["payload"], dict)
    assert captured["session"] == "session-1"
