from datetime import datetime, UTC, timedelta
import logging

import pytest
from fastapi import HTTPException

from issue_solver.events.domain import (
    NotionIntegrationAuthorized,
    NotionIntegrationAuthorizationFailed,
    NotionIntegrationTokenRefreshed,
)
from issue_solver.events.event_store import InMemoryEventStore
from issue_solver.events.notion_integration import NotionCredentials
from issue_solver.webapi.routers import notion_integration

try:
    from tests.controllable_clock import ControllableClock  # type: ignore
except ModuleNotFoundError:
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from controllable_clock import ControllableClock  # type: ignore


@pytest.fixture(autouse=True)
def configure_env(monkeypatch):
    notion_integration._get_mcp_settings.cache_clear()
    monkeypatch.setenv("NOTION_MCP_CLIENT_ID", "stub-mcp-client-id")
    monkeypatch.setenv("NOTION_MCP_CLIENT_SECRET", "stub-mcp-client-secret")
    monkeypatch.setenv("NOTION_MCP_OAUTH_REDIRECT_URI", "https://example.com/callback")
    monkeypatch.setenv("NOTION_MCP_RETURN_BASE_URL", "https://frontend.example.com")
    yield
    notion_integration._get_mcp_settings.cache_clear()


@pytest.mark.asyncio
async def test_refresh_emits_rotation_event(monkeypatch):
    # Given
    event_store = InMemoryEventStore()
    clock = ControllableClock(datetime(2025, 10, 31, 15, 0, tzinfo=UTC))
    base_event = NotionIntegrationAuthorized(
        occurred_at=clock.now(),
        user_id="user",
        space_id="space",
        process_id="process",
        workspace_id="workspace",
        workspace_name="Workspace",
        bot_id="bot",
        mcp_access_token="mcp-old",
        mcp_refresh_token="mcp-refresh",
        mcp_token_expires_at=clock.now() + timedelta(seconds=10),
    )
    await event_store.append(base_event.process_id, base_event)

    credentials = NotionCredentials(
        mcp_access_token="mcp-old",
        mcp_refresh_token="mcp-refresh",
        mcp_token_expires_at=clock.now() + timedelta(seconds=10),
        workspace_id="workspace",
        workspace_name="Workspace",
        bot_id="bot",
        process_id=base_event.process_id,
    )

    async def fake_request(**_kwargs):
        return {
            "access_token": "mcp-new",
            "refresh_token": "mcp-refresh",
            "expires_in": 3600,
            "workspace_id": "workspace",
            "workspace_name": "Workspace",
            "bot_id": "bot",
        }

    monkeypatch.setattr(notion_integration, "_request_oauth_token", fake_request)

    # When
    refreshed = await notion_integration.ensure_fresh_notion_credentials(
        event_store=event_store,
        credentials=credentials,
        space_id="space",
        user_id="user",
        clock=clock,
        logger=logging.getLogger("test"),
    )

    # Then
    events = await event_store.get(base_event.process_id)
    rotation = next(e for e in events if isinstance(e, NotionIntegrationTokenRefreshed))
    assert rotation.mcp_access_token == "mcp-new"
    assert rotation.mcp_refresh_token == "mcp-refresh"
    assert refreshed.mcp_access_token == "mcp-new"
    assert refreshed.mcp_token_expires_at is not None


@pytest.mark.asyncio
async def test_refresh_records_failure(monkeypatch):
    # Given
    event_store = InMemoryEventStore()
    clock = ControllableClock(datetime(2025, 10, 31, 15, 0, tzinfo=UTC))
    base_event = NotionIntegrationAuthorized(
        occurred_at=clock.now(),
        user_id="user",
        space_id="space",
        process_id="process",
        workspace_id="workspace",
        workspace_name="Workspace",
        bot_id="bot",
        mcp_access_token="mcp-old",
        mcp_refresh_token="mcp-refresh",
        mcp_token_expires_at=clock.now() + timedelta(seconds=10),
    )
    await event_store.append(base_event.process_id, base_event)

    credentials = NotionCredentials(
        mcp_access_token="mcp-old",
        mcp_refresh_token="mcp-refresh",
        mcp_token_expires_at=clock.now() + timedelta(seconds=10),
        workspace_id="workspace",
        workspace_name="Workspace",
        bot_id="bot",
        process_id=base_event.process_id,
    )

    async def failure(**_kwargs):
        raise HTTPException(status_code=400, detail={"error": "invalid_grant"})

    monkeypatch.setattr(notion_integration, "_request_oauth_token", failure)

    # When / Then
    with pytest.raises(HTTPException) as exc:
        await notion_integration.ensure_fresh_notion_credentials(
            event_store=event_store,
            credentials=credentials,
            space_id="space",
            user_id="user",
            clock=clock,
            logger=logging.getLogger("test"),
        )

    assert exc.value.status_code == 401
    events = await event_store.get(base_event.process_id)
    failure_event = next(
        e for e in events if isinstance(e, NotionIntegrationAuthorizationFailed)
    )
    assert failure_event.error_type == "invalid_grant"
