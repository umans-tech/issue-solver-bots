import logging
import uuid
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException

from issue_solver.clock import Clock
from issue_solver.events.domain import (
    NotionIntegrationConnected,
    NotionIntegrationTokenRotated,
)
from issue_solver.events.event_store import EventStore
from issue_solver.events.notion_integration import (
    get_notion_credentials,
    get_notion_integration_event,
)
from issue_solver.webapi.dependencies import (
    get_clock,
    get_event_store,
    get_logger,
    get_user_id_or_default,
)
from issue_solver.webapi.payloads import (
    ConnectNotionIntegrationRequest,
    NotionIntegrationView,
    RotateNotionIntegrationRequest,
)

NOTION_API_BASE_URL = "https://api.notion.com/v1"
NOTION_MCP_VERSION = "2022-06-28"

router = APIRouter(prefix="/integrations/notion", tags=["notion-integrations"])


async def _validate_notion_token(access_token: str) -> dict:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Notion-Version": NOTION_MCP_VERSION,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{NOTION_API_BASE_URL}/users/me", headers=headers)

    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Invalid Notion access token")
    if response.status_code == 403:
        raise HTTPException(
            status_code=403, detail="Notion token lacks required permissions"
        )
    if not response.is_success:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to validate Notion token: {response.text}",
        )

    return response.json()


def _extract_workspace_metadata(
    user_payload: dict,
) -> tuple[str | None, str | None, str | None]:
    bot_info = user_payload.get("bot", {}) if isinstance(user_payload, dict) else {}
    workspace_id = bot_info.get("workspace_id") or user_payload.get("workspace_id")
    workspace_name = bot_info.get("workspace_name") or user_payload.get("name")
    bot_id = user_payload.get("id")
    return workspace_id, workspace_name, bot_id


@router.post("/", status_code=201)
async def connect_notion_integration(
    request: ConnectNotionIntegrationRequest,
    user_id: Annotated[str, Depends(get_user_id_or_default)],
    event_store: Annotated[EventStore, Depends(get_event_store)],
    clock: Annotated[Clock, Depends(get_clock)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(lambda: get_logger("issue_solver.webapi.routers.notion.connect")),
    ],
) -> NotionIntegrationView:
    logger.info(
        "Connecting Notion integration for space %s (user=%s)",
        request.space_id,
        user_id,
    )

    user_payload = await _validate_notion_token(request.access_token)
    workspace_id, workspace_name, bot_id = _extract_workspace_metadata(user_payload)

    process_id = str(uuid.uuid4())
    occurred_at = clock.now()

    event = NotionIntegrationConnected(
        occurred_at=occurred_at,
        access_token=request.access_token,
        user_id=user_id,
        space_id=request.space_id,
        process_id=process_id,
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        bot_id=bot_id,
    )

    await event_store.append(process_id, event)

    logger.info(
        "Notion integration connected for space %s (process=%s)",
        request.space_id,
        process_id,
    )

    return NotionIntegrationView(
        space_id=request.space_id,
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        bot_id=bot_id,
        connected_at=occurred_at,
        process_id=process_id,
        has_valid_token=True,
    )


@router.put("/{space_id}/token", status_code=200)
async def rotate_notion_token(
    space_id: str,
    request: RotateNotionIntegrationRequest,
    user_id: Annotated[str, Depends(get_user_id_or_default)],
    event_store: Annotated[EventStore, Depends(get_event_store)],
    clock: Annotated[Clock, Depends(get_clock)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(lambda: get_logger("issue_solver.webapi.routers.notion.rotate")),
    ],
) -> NotionIntegrationView:
    integration = await get_notion_integration_event(event_store, space_id)
    if not integration:
        raise HTTPException(
            status_code=404,
            detail=f"No Notion integration configured for space {space_id}",
        )

    logger.info(
        "Rotating Notion token for space %s (process=%s, user=%s)",
        space_id,
        integration.process_id,
        user_id,
    )

    user_payload = await _validate_notion_token(request.access_token)
    workspace_id, workspace_name, bot_id = _extract_workspace_metadata(user_payload)

    event = NotionIntegrationTokenRotated(
        occurred_at=clock.now(),
        new_access_token=request.access_token,
        user_id=user_id,
        space_id=space_id,
        process_id=integration.process_id,
    )
    await event_store.append(integration.process_id, event)

    return NotionIntegrationView(
        space_id=space_id,
        workspace_id=workspace_id or integration.workspace_id,
        workspace_name=workspace_name or integration.workspace_name,
        bot_id=bot_id or integration.bot_id,
        connected_at=integration.occurred_at,
        process_id=integration.process_id,
        has_valid_token=True,
    )


@router.get("/{space_id}", status_code=200)
async def get_notion_integration(
    space_id: str,
    event_store: Annotated[EventStore, Depends(get_event_store)],
) -> NotionIntegrationView:
    integration = await get_notion_integration_event(event_store, space_id)
    if not integration:
        raise HTTPException(
            status_code=404,
            detail=f"No Notion integration configured for space {space_id}",
        )

    return NotionIntegrationView(
        space_id=space_id,
        workspace_id=integration.workspace_id,
        workspace_name=integration.workspace_name,
        bot_id=integration.bot_id,
        connected_at=integration.occurred_at,
        process_id=integration.process_id,
        has_valid_token=await get_notion_credentials(event_store, space_id) is not None,
    )
