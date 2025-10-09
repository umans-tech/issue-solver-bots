from dataclasses import dataclass
from typing import Sequence

from issue_solver.events.domain import (
    DomainEvent,
    NotionIntegrationConnected,
    NotionIntegrationTokenRotated,
    most_recent_event,
)
from issue_solver.events.event_store import EventStore


@dataclass(kw_only=True)
class NotionCredentials:
    access_token: str
    workspace_id: str | None
    workspace_name: str | None
    bot_id: str | None


async def get_notion_integration_event(
    event_store: EventStore, space_id: str
) -> NotionIntegrationConnected | None:
    events = await event_store.find({"space_id": space_id}, NotionIntegrationConnected)
    return most_recent_event(events, NotionIntegrationConnected)


async def get_notion_credentials(
    event_store: EventStore, space_id: str
) -> NotionCredentials | None:
    notion_connected = await get_notion_integration_event(event_store, space_id)
    if not notion_connected:
        return None

    access_token = await get_notion_access_token(
        event_store, notion_connected.process_id
    )
    if not access_token:
        return None

    return NotionCredentials(
        access_token=access_token,
        workspace_id=notion_connected.workspace_id,
        workspace_name=notion_connected.workspace_name,
        bot_id=notion_connected.bot_id,
    )


async def get_notion_access_token(
    event_store: EventStore, process_id: str
) -> str | None:
    events = await event_store.get(process_id)
    return get_most_recent_notion_token(events)


def get_most_recent_notion_token(domain_events: Sequence[DomainEvent]) -> str | None:
    rotated = most_recent_event(domain_events, NotionIntegrationTokenRotated)
    connected = most_recent_event(domain_events, NotionIntegrationConnected)

    if rotated and connected:
        return (
            rotated.new_access_token
            if rotated.occurred_at >= connected.occurred_at
            else connected.access_token
        )

    if rotated:
        return rotated.new_access_token

    if connected:
        return connected.access_token

    return None


async def fetch_notion_credentials(
    event_store: EventStore, space_id: str
) -> NotionCredentials:
    credentials = await get_notion_credentials(event_store, space_id)
    if not credentials:
        raise RuntimeError(f"No Notion integration connected for space {space_id}")
    return credentials
