from __future__ import annotations

import httpx
import pytest

from issue_solver.events.domain import CodeRepositoryConnected


async def _simulate_network_failure(
    self,  # noqa: D401 - matches AsyncClient signature
    url: str,
    *args,
    **kwargs,
) -> httpx.Response:
    request = httpx.Request("POST", url)
    raise httpx.RequestError("connection failed", request=request)


@pytest.fixture
def github_mcp_network_failure(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(httpx.AsyncClient, "post", _simulate_network_failure)


def test_github_mcp_proxy_returns_400_when_space_id_is_missing(api_client) -> None:
    # When
    response = api_client.post(
        "/mcp/repositories/proxy",
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


def test_github_mcp_proxy_returns_404_when_space_has_no_repository(api_client) -> None:
    # When
    response = api_client.post(
        "/mcp/repositories/proxy",
        json={
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1,
            "meta": {"user_id": "user-123", "space_id": "space-without-repo"},
        },
    )

    # Then
    assert response.status_code == 404
    assert "No repository connected to this space" in response.json()["detail"]


def test_github_mcp_proxy_returns_401_when_access_token_is_missing(
    api_client,
    time_under_control,
) -> None:
    # Given
    time_under_control.set_from_iso_format("2025-10-31T14:00:00")
    space_id = "space-empty-token"
    process_id = "process-empty-token"
    event_store = api_client.app.state.event_store

    api_client.portal.call(
        event_store.append,
        process_id,
        CodeRepositoryConnected(
            url="https://github.com/example/repo.git",
            access_token="   ",
            user_id="user-empty-token",
            space_id=space_id,
            knowledge_base_id="kb-empty-token",
            process_id=process_id,
            occurred_at=time_under_control.now(),
            token_permissions=None,
        ),
    )

    # When
    response = api_client.post(
        "/mcp/repositories/proxy",
        json={
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1,
            "meta": {"user_id": "user-empty-token", "space_id": space_id},
        },
    )

    # Then
    assert response.status_code == 401
    assert "No valid access token" in response.json()["detail"]


def test_github_mcp_proxy_returns_503_when_remote_service_is_unreachable(
    api_client,
    time_under_control,
    github_mcp_network_failure,
) -> None:
    # Given
    time_under_control.set_from_iso_format("2025-10-31T14:30:00")
    space_id = "space-remote-failure"
    process_id = "process-remote-failure"
    event_store = api_client.app.state.event_store

    api_client.portal.call(
        event_store.append,
        process_id,
        CodeRepositoryConnected(
            url="https://github.com/example/repo.git",
            access_token="ghp_valid_token",
            user_id="user-remote-failure",
            space_id=space_id,
            knowledge_base_id="kb-remote-failure",
            process_id=process_id,
            occurred_at=time_under_control.now(),
            token_permissions=None,
        ),
    )

    # When
    response = api_client.post(
        "/mcp/repositories/proxy",
        json={
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1,
            "meta": {"user_id": "user-remote-failure", "space_id": space_id},
        },
    )

    # Then
    assert response.status_code == 503
    assert "Unable to connect to GitHub MCP server" in response.json()["detail"]
