from dataclasses import dataclass
from datetime import datetime
from typing import Self

from issue_solver.events.domain import (
    NotionIntegrationAuthorized,
    NotionIntegrationTokenRefreshed,
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

    @classmethod
    def create_from(
        cls,
        integration_event: NotionIntegrationAuthorized
        | NotionIntegrationTokenRefreshed,
    ) -> Self:
        return cls(
            mcp_access_token=integration_event.mcp_access_token,
            mcp_refresh_token=integration_event.mcp_refresh_token,
            mcp_token_expires_at=integration_event.mcp_token_expires_at,
            workspace_id=integration_event.workspace_id,
            workspace_name=integration_event.workspace_name,
            bot_id=integration_event.bot_id,
            process_id=integration_event.process_id,
        )


async def get_notion_integration_event(
    event_store: EventStore, space_id: str
) -> NotionIntegrationAuthorized | None:
    events = await event_store.find({"space_id": space_id}, NotionIntegrationAuthorized)
    return most_recent_event(events, NotionIntegrationAuthorized)


async def get_integration_by_process(
    event_store: EventStore, process_id: str
) -> NotionIntegrationAuthorized | None:
    events = await event_store.get(process_id)
    return most_recent_event(events, NotionIntegrationAuthorized)


async def get_notion_credentials(
    event_store: EventStore, space_id: str
) -> NotionCredentials | None:
    notion_connected = await get_notion_integration_event(event_store, space_id)
    if not notion_connected:
        return None

    events = await event_store.get(notion_connected.process_id)
    latest_rotation = most_recent_event(events, NotionIntegrationTokenRefreshed)
    if latest_rotation and latest_rotation.occurred_at > notion_connected.occurred_at:
        return NotionCredentials.create_from(latest_rotation)
    return NotionCredentials.create_from(notion_connected)


async def fetch_notion_credentials(
    event_store: EventStore, space_id: str
) -> NotionCredentials:
    credentials = await get_notion_credentials(event_store, space_id)
    if not credentials:
        raise RuntimeError(f"No Notion integration connected for space {space_id}")
    return credentials
