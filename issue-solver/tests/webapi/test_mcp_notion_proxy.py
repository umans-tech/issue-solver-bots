"""Tests for Notion MCP proxy functionality."""

import pytest
from starlette.testclient import TestClient

from issue_solver.webapi.routers import notion_integration, mcp_notion_proxy


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

    connect_response = api_client.post(
        "/integrations/notion/",
        json={"access_token": "secret", "space_id": space_id},
        headers={"X-User-ID": user_id},
    )
    assert connect_response.status_code == 201

    captured: dict[str, object | None] = {}

    async def fake_forward(token: str, payload: dict, session_id: str | None):
        captured["token"] = token
        captured["payload"] = payload
        captured["session"] = session_id
        return {"status": "ok"}, session_id or "session-generated"

    monkeypatch.setattr(mcp_notion_proxy, "_forward_to_notion", fake_forward)

    response = api_client.post(
        "/mcp/notion/proxy",
        json={"meta": {"user_id": user_id, "space_id": space_id}},
        headers={"mcp-session-id": "session-1"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["mcp-session-id"] == "session-1"
    assert captured["token"] == "secret"
    assert isinstance(captured["payload"], dict)
    assert captured["session"] == "session-1"
