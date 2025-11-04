"""Notion MCP Proxy Router for Issue Solver."""

import logging
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import Response

from issue_solver.clock import Clock
from issue_solver.events.event_store import EventStore
from issue_solver.events.notion_integration import get_notion_credentials
from issue_solver.webapi.dependencies import get_clock, get_event_store, get_logger
from issue_solver.webapi.routers.notion_integration import (
    MCP_RECONNECT_MESSAGE,
    ensure_fresh_notion_credentials,
)

NOTION_MCP_REMOTE_ENDPOINT = "https://mcp.notion.com/mcp"
NOTION_VERSION = "2025-09-03"

router = APIRouter()


@router.post("/mcp/notion/proxy")
async def proxy_notion_mcp(
    raw_request: Request,
    event_store: Annotated[EventStore, Depends(get_event_store)],
    clock: Annotated[Clock, Depends(get_clock)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(lambda: get_logger("issue_solver.webapi.routers.notion_mcp")),
    ],
) -> Response:
    logger.info("Processing Notion MCP proxy request")
    try:
        payload: dict[str, Any] = await raw_request.json()
        incoming_session_id: str | None = raw_request.headers.get("mcp-session-id")
        user_id = payload.get("meta", {}).get("user_id")
        space_id = payload.get("meta", {}).get("space_id")

        if not space_id:
            raise HTTPException(
                status_code=400,
                detail="Missing space_id. MCP tools require a valid space context.",
            )

        notion_credentials = await get_notion_credentials(event_store, space_id)
        if not notion_credentials:
            raise HTTPException(
                status_code=404,
                detail="No Notion integration connected to this space. Please connect Notion to enable MCP tools.",
            )

        notion_credentials = await ensure_fresh_notion_credentials(
            event_store=event_store,
            credentials=notion_credentials,
            space_id=space_id,
            user_id=user_id or "unknown-user-id",
            clock=clock,
            logger=logger,
        )

        effective_user_id = user_id or "unknown-user-id"

        logger.info(
            "Using Notion token for space %s (user=%s)",
            space_id,
            effective_user_id,
        )

        mcp_access_token = notion_credentials.mcp_access_token
        if not mcp_access_token:
            raise HTTPException(
                status_code=401,
                detail=MCP_RECONNECT_MESSAGE,
            )

        # Avoid forwarding proxy-specific metadata to Notion MCP API.
        notion_payload = dict(payload)
        notion_payload.pop("meta", None)
        logger.debug(
            "Forwarding Notion MCP payload with keys: %s",
            list(notion_payload.keys()),
        )

        logger.debug(
            "Forwarding Notion MCP request for space %s with MCP token len=%d",
            space_id,
            len(mcp_access_token),
        )

        http_response, outgoing_session_id = await _forward_to_notion(
            NOTION_MCP_REMOTE_ENDPOINT,
            mcp_access_token,
            notion_payload,
            incoming_session_id,
        )

        content_type = http_response.headers.get("content-type")
        response_json = Response(
            content=http_response.content,
            media_type=content_type,
            status_code=http_response.status_code,
        )
        if outgoing_session_id:
            response_json.headers["mcp-session-id"] = outgoing_session_id
        return response_json

    except httpx.RequestError as exc:
        logger.error("Network error connecting to Notion MCP server: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to Notion MCP server. Please try again later.",
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive catch
        logger.error("Unexpected error in Notion MCP proxy: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while processing Notion MCP request.",
        )


async def _forward_to_notion(
    endpoint: str,
    access_token: str,
    payload: dict[str, Any],
    incoming_session_id: str | None,
) -> tuple[httpx.Response, str | None]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "Issue-Solver-Notion-MCP-Proxy/1.0",
        "Notion-Version": NOTION_VERSION,
        "Accept": "application/json, text/event-stream",
    }
    if incoming_session_id:
        headers["mcp-session-id"] = incoming_session_id

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logging.getLogger("issue_solver.webapi.routers.notion_mcp").debug(
                "Forwarding Notion MCP request with token prefix %s (len=%d)",
                access_token[:6],
                len(access_token),
            )
            response = await client.post(endpoint, json=payload, headers=headers)
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503,
                detail="Unable to connect to Notion MCP server. Please try again later.",
            ) from exc

    if not response.is_success:
        error_text = response.text
        error_summary: Any = None
        try:
            error_summary = response.json()
        except ValueError:
            error_summary = error_text
        auth_header = response.headers.get("www-authenticate")

        logging.getLogger("issue_solver.webapi.routers.notion_mcp").warning(
            "Notion MCP returned %s: %s (auth header=%s)",
            response.status_code,
            error_summary,
            auth_header,
        )

        if response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail=(
                    "Notion MCP authentication failed. Reconnect Notion from the Issue "
                    "Solver integrations page to refresh permissions."
                ),
            )

        raise HTTPException(
            status_code=response.status_code,
            detail=f"Notion MCP server error: {error_text}",
        )

    return response, response.headers.get("mcp-session-id")


def _detail_indicates_invalid_grant(detail: Any) -> bool:
    text = ""
    if isinstance(detail, dict):
        text = " ".join(str(value) for value in detail.values())
    else:
        text = str(detail)
    return "invalid_grant" in text.lower()
