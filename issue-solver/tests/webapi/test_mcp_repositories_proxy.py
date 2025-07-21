"""Tests for MCP Repositories Proxy functionality."""

from starlette.testclient import TestClient


def test_mcp_proxy_missing_space_id(api_client: TestClient):
    """Test that MCP proxy returns 400 when space_id is missing."""
    # Arrange
    payload = {
        "meta": {
            "user_id": "user-123"
            # Missing space_id
        },
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1,
    }

    # Act
    response = api_client.post("/mcp/repositories/proxy", json=payload)

    # Assert
    assert response.status_code == 400
    assert "Missing space_id" in response.json()["detail"]


def test_mcp_proxy_no_repo_connected(api_client: TestClient):
    """Test that MCP proxy returns 404 when no repository is connected to the space."""
    # Arrange
    payload = {
        "meta": {"user_id": "user-123", "space_id": "space-without-repo"},
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1,
    }

    # Act
    response = api_client.post("/mcp/repositories/proxy", json=payload)

    # Assert
    assert response.status_code == 404
    assert "No repository connected to this space" in response.json()["detail"]
