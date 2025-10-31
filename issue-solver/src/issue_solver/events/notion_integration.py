from dataclasses import dataclass
from datetime import datetime

from issue_solver.events.domain import (
    NotionIntegrationConnected,
    NotionIntegrationFailed,
    NotionIntegrationTokenRotated,
    most_recent_event,
)
from issue_solver.events.event_store import EventStore


@dataclass(kw_only=True)
class NotionCredentials:
    mcp_access_token: str | None
    mcp_refresh_token: str | None
    mcp_token_expires_at: datetime | None
    workspace_id: str | None
    workspace_name: str | None
    bot_id: str | None
    process_id: str


async def get_notion_integration_event(
    event_store: EventStore, space_id: str
) -> NotionIntegrationConnected | None:
    events = await event_store.find({"space_id": space_id}, NotionIntegrationConnected)
    return most_recent_event(events, NotionIntegrationConnected)


async def get_integration_by_process(
    event_store: EventStore, process_id: str
) -> NotionIntegrationConnected | None:
    events = await event_store.get(process_id)
    return most_recent_event(events, NotionIntegrationConnected)


async def get_notion_credentials(
    event_store: EventStore, space_id: str
) -> NotionCredentials | None:
    notion_connected = await get_notion_integration_event(event_store, space_id)
    if not notion_connected:
        return None

    events = await event_store.get(notion_connected.process_id)
    latest_rotation = most_recent_event(events, NotionIntegrationTokenRotated)
    latest_failure = most_recent_event(events, NotionIntegrationFailed)

    credentials = _latest_mcp_credentials(
        base_event=notion_connected,
        rotation=latest_rotation,
        failure=latest_failure,
    )
    return credentials


def _latest_mcp_credentials(
    *,
    base_event: NotionIntegrationConnected,
    rotation: NotionIntegrationTokenRotated | None,
    failure: NotionIntegrationFailed | None,
) -> NotionCredentials | None:
    current_time = base_event.occurred_at
    access_token = base_event.mcp_access_token
    refresh_token = base_event.mcp_refresh_token
    expires_at = base_event.mcp_token_expires_at
    workspace_id = base_event.workspace_id
    workspace_name = base_event.workspace_name
    bot_id = base_event.bot_id

    if rotation and rotation.occurred_at >= current_time:
        current_time = rotation.occurred_at
        access_token = rotation.new_mcp_access_token
        refresh_token = rotation.new_mcp_refresh_token
        expires_at = rotation.mcp_token_expires_at
        workspace_id = rotation.workspace_id or workspace_id
        workspace_name = rotation.workspace_name or workspace_name
        bot_id = rotation.bot_id or bot_id

    if failure and failure.occurred_at >= current_time:
        return None

    if not refresh_token:
        return None

    resolved_workspace_id = workspace_id or bot_id

    return NotionCredentials(
        mcp_access_token=access_token,
        mcp_refresh_token=refresh_token,
        mcp_token_expires_at=expires_at,
        workspace_id=resolved_workspace_id,
        workspace_name=workspace_name,
        bot_id=bot_id,
        process_id=base_event.process_id,
    )


async def fetch_notion_credentials(
    event_store: EventStore, space_id: str
) -> NotionCredentials:
    credentials = await get_notion_credentials(event_store, space_id)
    if not credentials:
        raise RuntimeError(f"No Notion integration connected for space {space_id}")
    return credentials
