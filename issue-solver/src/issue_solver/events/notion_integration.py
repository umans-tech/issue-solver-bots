import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, Sequence

from issue_solver.events.domain import (
    DomainEvent,
    NotionIntegrationConnected,
    NotionIntegrationTokenRotated,
    most_recent_event,
)
from issue_solver.events.event_store import EventStore


logger = logging.getLogger("issue_solver.events.notion_integration")


@dataclass(kw_only=True)
class NotionCredentials:
    access_token: str
    refresh_token: str | None
    token_expires_at: datetime | None
    workspace_id: str | None
    workspace_name: str | None
    bot_id: str | None
    process_id: str
    auth_mode: Literal["manual", "oauth"] = "manual"


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
    (
        access_token,
        refresh_token,
        token_expires_at,
    ) = get_most_recent_notion_token(events)
    if not access_token:
        return None

    latest_rotation = most_recent_event(events, NotionIntegrationTokenRotated)

    workspace_id = (
        latest_rotation.workspace_id
        if latest_rotation
        else notion_connected.workspace_id
    )
    workspace_name = (
        latest_rotation.workspace_name
        if latest_rotation and latest_rotation.workspace_name
        else notion_connected.workspace_name
    )
    bot_id = (
        latest_rotation.bot_id
        if latest_rotation and latest_rotation.bot_id
        else notion_connected.bot_id
    )

    if not workspace_id:
        # attempt to backfill workspace metadata by validating the token again
        try:
            from issue_solver.webapi.routers.notion_integration import (
                _validate_notion_token,
            )

            payload = await _validate_notion_token(access_token)
        except Exception:  # pragma: no cover - defensive fallback
            payload = None

        payload_dict: dict[str, Any] | None = (
            payload if isinstance(payload, dict) else None
        )

        if payload_dict:
            logger.debug("Fetched Notion user payload for backfill: %s", payload_dict)
            raw_bot = payload_dict.get("bot")
            bot_info = raw_bot if isinstance(raw_bot, dict) else {}
            if bot_info:
                logger.debug("Notion bot info: %s", bot_info)

            raw_owner = payload_dict.get("owner")
            owner_info = raw_owner if isinstance(raw_owner, dict) else {}
            if owner_info:
                logger.debug("Notion owner info: %s", owner_info)

            workspace_id = (
                bot_info.get("workspace_id")
                or owner_info.get("workspace_id")
                or payload_dict.get("workspace_id")
                or workspace_id
            )
            workspace_name = (
                bot_info.get("workspace_name")
                or payload_dict.get("name")
                or workspace_name
            )
            bot_id = payload_dict.get("id") or bot_info.get("id") or bot_id

    if not workspace_id and bot_id:
        workspace_id = bot_id

    return NotionCredentials(
        access_token=access_token,
        refresh_token=refresh_token,
        token_expires_at=token_expires_at,
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        bot_id=bot_id,
        process_id=notion_connected.process_id,
        auth_mode=(
            latest_rotation.auth_mode if latest_rotation else notion_connected.auth_mode
        ),
    )


def get_most_recent_notion_token(
    domain_events: Sequence[DomainEvent],
) -> tuple[str | None, str | None, datetime | None]:
    rotated = most_recent_event(domain_events, NotionIntegrationTokenRotated)
    connected = most_recent_event(domain_events, NotionIntegrationConnected)

    if rotated and connected:
        if rotated.occurred_at >= connected.occurred_at:
            return (
                rotated.new_access_token,
                rotated.new_refresh_token,
                rotated.token_expires_at,
            )
        return (
            connected.access_token,
            connected.refresh_token,
            connected.token_expires_at,
        )

    if rotated:
        return (
            rotated.new_access_token,
            rotated.new_refresh_token,
            rotated.token_expires_at,
        )

    if connected:
        return (
            connected.access_token,
            connected.refresh_token,
            connected.token_expires_at,
        )

    return (None, None, None)


async def fetch_notion_credentials(
    event_store: EventStore, space_id: str
) -> NotionCredentials:
    credentials = await get_notion_credentials(event_store, space_id)
    if not credentials:
        raise RuntimeError(f"No Notion integration connected for space {space_id}")
    return credentials
