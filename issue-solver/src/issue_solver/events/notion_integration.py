from dataclasses import dataclass
from datetime import datetime

from issue_solver.events.domain import (
    NotionIntegrationConnected,
    NotionIntegrationTokenRotated,
    most_recent_event,
)
from issue_solver.events.event_store import EventStore


@dataclass(kw_only=True)
class NotionCredentials:
    access_token: str | None
    refresh_token: str | None
    token_expires_at: datetime | None
    mcp_access_token: str | None = None
    mcp_refresh_token: str | None = None
    mcp_token_expires_at: datetime | None = None
    workspace_id: str | None = None
    workspace_name: str | None = None
    bot_id: str | None = None
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

    use_rotation = (
        latest_rotation is not None
        and latest_rotation.occurred_at >= notion_connected.occurred_at
    )

    if use_rotation and latest_rotation:
        access_token = latest_rotation.new_access_token
        refresh_token = latest_rotation.new_refresh_token
        token_expires_at = latest_rotation.token_expires_at
        mcp_access_token = latest_rotation.new_mcp_access_token
        mcp_refresh_token = latest_rotation.new_mcp_refresh_token
        mcp_token_expires_at = latest_rotation.mcp_token_expires_at
        workspace_id = latest_rotation.workspace_id or notion_connected.workspace_id
        workspace_name = (
            latest_rotation.workspace_name or notion_connected.workspace_name
        )
        bot_id = latest_rotation.bot_id or notion_connected.bot_id
    else:
        access_token = notion_connected.access_token
        refresh_token = notion_connected.refresh_token
        token_expires_at = notion_connected.token_expires_at
        mcp_access_token = notion_connected.mcp_access_token
        mcp_refresh_token = notion_connected.mcp_refresh_token
        mcp_token_expires_at = notion_connected.mcp_token_expires_at
        workspace_id = notion_connected.workspace_id
        workspace_name = notion_connected.workspace_name
        bot_id = notion_connected.bot_id

    if not access_token and not mcp_refresh_token:
        return None

    if not workspace_id and bot_id:
        workspace_id = bot_id

    return NotionCredentials(
        access_token=access_token,
        refresh_token=refresh_token,
        token_expires_at=token_expires_at,
        mcp_access_token=mcp_access_token,
        mcp_refresh_token=mcp_refresh_token,
        mcp_token_expires_at=mcp_token_expires_at,
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        bot_id=bot_id,
        process_id=notion_connected.process_id,
    )


async def fetch_notion_credentials(
    event_store: EventStore, space_id: str
) -> NotionCredentials:
    credentials = await get_notion_credentials(event_store, space_id)
    if not credentials:
        raise RuntimeError(f"No Notion integration connected for space {space_id}")
    return credentials
