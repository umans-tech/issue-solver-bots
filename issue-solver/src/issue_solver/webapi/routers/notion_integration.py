import base64
import json
import logging
import os
import secrets
import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Annotated, Any
from urllib.parse import urlencode, urljoin, urlparse, parse_qsl, urlunparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from redis import Redis

from issue_solver.clock import Clock
from issue_solver.events.domain import (
    NotionIntegrationConnected,
    NotionIntegrationTokenRotated,
)
from issue_solver.events.event_store import EventStore
from issue_solver.events.notion_integration import (
    NotionCredentials,
    get_notion_credentials,
    get_notion_integration_event,
)
from issue_solver.webapi.dependencies import (
    get_clock,
    get_event_store,
    get_logger,
    get_redis_client,
    get_user_id_or_default,
)
from issue_solver.webapi.payloads import (
    ConnectNotionIntegrationRequest,
    NotionIntegrationView,
    RotateNotionIntegrationRequest,
)

NOTION_API_BASE_URL = "https://api.notion.com/v1"
NOTION_API_RESOURCE = "https://api.notion.com"
NOTION_MCP_VERSION = "2022-06-28"
NOTION_MCP_RESOURCE = "https://mcp.notion.com"
NOTION_MCP_AUTH_SERVER_METADATA_URL = (
    "https://mcp.notion.com/.well-known/oauth-authorization-server"
)

router = APIRouter(prefix="/integrations/notion", tags=["notion-integrations"])

module_logger = logging.getLogger("issue_solver.webapi.routers.notion_integration")

NOTION_OAUTH_AUTHORIZE_URL = f"{NOTION_API_BASE_URL}/oauth/authorize"
NOTION_OAUTH_TOKEN_URL = f"{NOTION_API_BASE_URL}/oauth/token"
OAUTH_STATE_CACHE_PREFIX = "notion:oauth:state:"
DEFAULT_RETURN_PATH = "/integrations/notion/callback"
MCP_OAUTH_STATE_CACHE_PREFIX = "notion:mcp:oauth:state:"
MCP_DEFAULT_REDIRECT_PATH = "/integrations/notion/mcp/oauth/callback"


@dataclass(frozen=True)
class NotionOAuthConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    return_base_url: str | None
    state_ttl_seconds: int
    mcp_client_id: str | None
    mcp_client_secret: str | None
    mcp_token_endpoint: str
    mcp_scope: str | None
    mcp_token_auth_method: str
    api_resource: str | None
    mcp_resource: str | None
    mcp_registration_endpoint: str | None
    mcp_client_name: str | None
    mcp_authorize_endpoint: str
    mcp_redirect_uri: str


_OAUTH_CONFIG: NotionOAuthConfig | None = None
_MCP_AUTH_SERVER_METADATA: dict[str, Any] | None = None


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


async def _upsert_notion_integration(
    *,
    access_token: str,
    refresh_token: str | None,
    expires_in: int | None,
    mcp_access_token: str | None,
    mcp_refresh_token: str | None,
    mcp_expires_in: int | None,
    space_id: str,
    user_id: str,
    workspace_id: str | None,
    workspace_name: str | None,
    bot_id: str | None,
    event_store: EventStore,
    clock: Clock,
    logger: logging.Logger | logging.LoggerAdapter,
) -> NotionIntegrationView:
    integration = await get_notion_integration_event(event_store, space_id)
    now = clock.now()
    token_expires_at = (
        now + timedelta(seconds=expires_in) if expires_in is not None else None
    )
    mcp_token_expires_at = (
        now + timedelta(seconds=mcp_expires_in) if mcp_expires_in is not None else None
    )

    resolved_workspace_id = workspace_id
    resolved_workspace_name = workspace_name
    resolved_bot_id = bot_id
    resolved_mcp_access_token = mcp_access_token
    resolved_mcp_refresh_token = mcp_refresh_token
    resolved_mcp_token_expires_at = mcp_token_expires_at
    if integration:
        resolved_workspace_id = resolved_workspace_id or integration.workspace_id
        resolved_workspace_name = resolved_workspace_name or integration.workspace_name
        resolved_bot_id = resolved_bot_id or integration.bot_id
        resolved_mcp_access_token = (
            resolved_mcp_access_token or integration.mcp_access_token
        )
        resolved_mcp_refresh_token = (
            resolved_mcp_refresh_token or integration.mcp_refresh_token
        )
        resolved_mcp_token_expires_at = (
            resolved_mcp_token_expires_at or integration.mcp_token_expires_at
        )

        if token_expires_at is None and integration.token_expires_at:
            token_expires_at = integration.token_expires_at

        rotation_event = NotionIntegrationTokenRotated(
            occurred_at=now,
            new_access_token=access_token,
            new_refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            user_id=user_id,
            space_id=space_id,
            process_id=integration.process_id,
            workspace_id=resolved_workspace_id,
            workspace_name=resolved_workspace_name,
            bot_id=resolved_bot_id,
            new_mcp_access_token=resolved_mcp_access_token,
            new_mcp_refresh_token=resolved_mcp_refresh_token,
            mcp_token_expires_at=resolved_mcp_token_expires_at,
        )
        await event_store.append(integration.process_id, rotation_event)
        process_id = integration.process_id
        connected_at = integration.occurred_at
        logger.info(
            "Updated Notion integration tokens for space %s (process=%s)",
            space_id,
            process_id,
        )
    else:
        process_id = str(uuid.uuid4())
        connected_event = NotionIntegrationConnected(
            occurred_at=now,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            user_id=user_id,
            space_id=space_id,
            process_id=process_id,
            workspace_id=resolved_workspace_id,
            workspace_name=resolved_workspace_name,
            bot_id=resolved_bot_id,
            mcp_access_token=resolved_mcp_access_token,
            mcp_refresh_token=resolved_mcp_refresh_token,
            mcp_token_expires_at=resolved_mcp_token_expires_at,
        )
        await event_store.append(process_id, connected_event)
        connected_at = now
        logger.info(
            "Notion integration connected for space %s (process=%s)",
            space_id,
            process_id,
        )

    return NotionIntegrationView(
        space_id=space_id,
        workspace_id=resolved_workspace_id,
        workspace_name=resolved_workspace_name,
        bot_id=resolved_bot_id,
        connected_at=connected_at,
        process_id=process_id,
        token_expires_at=token_expires_at,
        has_valid_token=True,
        has_mcp_token=resolved_mcp_refresh_token is not None,
    )


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

    return await _upsert_notion_integration(
        access_token=request.access_token,
        refresh_token=None,
        expires_in=None,
        mcp_access_token=None,
        mcp_refresh_token=None,
        mcp_expires_in=None,
        space_id=request.space_id,
        user_id=user_id,
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        bot_id=bot_id,
        event_store=event_store,
        clock=clock,
        logger=logger,
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

    now_ts = clock.now()
    mcp_expires_in: int | None = None
    if integration.mcp_token_expires_at and integration.mcp_token_expires_at > now_ts:
        mcp_expires_in = max(
            0,
            int((integration.mcp_token_expires_at - now_ts).total_seconds()),
        )

    return await _upsert_notion_integration(
        access_token=request.access_token,
        refresh_token=None,
        expires_in=None,
        mcp_access_token=integration.mcp_access_token,
        mcp_refresh_token=integration.mcp_refresh_token,
        mcp_expires_in=mcp_expires_in,
        space_id=space_id,
        user_id=user_id,
        workspace_id=workspace_id or integration.workspace_id,
        workspace_name=workspace_name or integration.workspace_name,
        bot_id=bot_id or integration.bot_id,
        event_store=event_store,
        clock=clock,
        logger=logger,
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

    credentials = await get_notion_credentials(event_store, space_id)
    workspace_id = (
        credentials.workspace_id
        if credentials and credentials.workspace_id
        else integration.workspace_id
    )
    workspace_name = (
        credentials.workspace_name
        if credentials and credentials.workspace_name
        else integration.workspace_name
    )
    bot_id = (
        credentials.bot_id if credentials and credentials.bot_id else integration.bot_id
    )
    token_expires_at = credentials.token_expires_at if credentials else None
    has_mcp_token = bool(credentials and credentials.mcp_refresh_token)

    return NotionIntegrationView(
        space_id=space_id,
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        bot_id=bot_id,
        connected_at=integration.occurred_at,
        process_id=integration.process_id,
        token_expires_at=token_expires_at,
        has_valid_token=credentials is not None,
        has_mcp_token=has_mcp_token,
    )


@router.get("/oauth/start", status_code=200)
async def start_notion_oauth_flow(
    user_id: Annotated[str, Depends(get_user_id_or_default)],
    redis_client: Annotated[Redis, Depends(get_redis_client)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(lambda: get_logger("issue_solver.webapi.routers.notion.oauth")),
    ],
    space_id: str = Query(..., alias="space_id"),
    return_path: str | None = Query(None, alias="return_path"),
) -> dict[str, str]:
    if not space_id:
        raise HTTPException(
            status_code=400, detail="space_id is required to begin the OAuth flow."
        )

    try:
        config = _get_oauth_config()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    normalized_return_path = _normalize_return_path(return_path)
    state = secrets.token_urlsafe(32)

    state_payload = {
        "space_id": space_id,
        "user_id": user_id or "unknown-user-id",
        "return_path": normalized_return_path,
    }
    redis_client.setex(
        _state_cache_key(state),
        config.state_ttl_seconds,
        json.dumps(state_payload),
    )

    authorize_params: dict[str, Any] = {
        "client_id": config.client_id,
        "response_type": "code",
        "owner": "user",
        "redirect_uri": config.redirect_uri,
        "state": state,
    }

    if config.api_resource:
        authorize_params["resource"] = config.api_resource

    authorize_url = f"{NOTION_OAUTH_AUTHORIZE_URL}?{urlencode(authorize_params)}"
    logger.info("Initiated Notion OAuth flow for space %s (user=%s)", space_id, user_id)
    return {"authorizeUrl": authorize_url, "state": state}


@router.get("/oauth/callback")
async def handle_notion_oauth_callback(
    redis_client: Annotated[Redis, Depends(get_redis_client)],
    event_store: Annotated[EventStore, Depends(get_event_store)],
    clock: Annotated[Clock, Depends(get_clock)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(lambda: get_logger("issue_solver.webapi.routers.notion.oauth")),
    ],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    try:
        config = _get_oauth_config()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not state:
        raise HTTPException(status_code=400, detail="Missing OAuth state parameter.")

    cached_state_raw = redis_client.get(_state_cache_key(state))
    if cached_state_raw is None:
        raise HTTPException(
            status_code=400, detail="Unknown or expired Notion OAuth state."
        )
    redis_client.delete(_state_cache_key(state))

    try:
        cached_state_bytes = (
            cached_state_raw
            if isinstance(cached_state_raw, (bytes, bytearray))
            else str(cached_state_raw).encode("utf-8")
        )
        state_payload = json.loads(cached_state_bytes.decode("utf-8"))
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=400, detail="Corrupted OAuth state payload."
        ) from exc

    space_id = state_payload.get("space_id")
    user_id = state_payload.get("user_id") or "unknown-user-id"
    return_path = state_payload.get("return_path") or DEFAULT_RETURN_PATH

    if not space_id:
        redirect_url = _build_return_url(
            config,
            return_path,
            {"status": "error", "error": "missing_space"},
        )
        return RedirectResponse(url=redirect_url, status_code=303)

    if error:
        redirect_url = _build_return_url(
            config,
            return_path,
            {"status": "error", "error": error},
        )
        return RedirectResponse(url=redirect_url, status_code=303)

    if not code:
        redirect_url = _build_return_url(
            config,
            return_path,
            {"status": "error", "error": "missing_code"},
        )
        return RedirectResponse(url=redirect_url, status_code=303)

    try:
        token_response = await _exchange_authorization_code(
            config=config,
            code=code,
            logger=logger,
        )
    except HTTPException as exc:
        redirect_url = _build_return_url(
            config,
            return_path,
            {"status": "error", "error": str(exc.detail)},
        )
        return RedirectResponse(url=redirect_url, status_code=303)

    access_token = token_response.get("access_token")
    if not access_token:
        redirect_url = _build_return_url(
            config,
            return_path,
            {"status": "error", "error": "missing_access_token"},
        )
        return RedirectResponse(url=redirect_url, status_code=303)

    existing_credentials = await get_notion_credentials(event_store, space_id)
    existing_mcp_access_token = (
        existing_credentials.mcp_access_token if existing_credentials else None
    )
    existing_mcp_refresh_token = (
        existing_credentials.mcp_refresh_token if existing_credentials else None
    )
    existing_mcp_expires_in: int | None = None
    now_ts = clock.now()
    if (
        existing_credentials
        and existing_credentials.mcp_token_expires_at
        and existing_credentials.mcp_token_expires_at > now_ts
    ):
        existing_mcp_expires_in = int(
            (existing_credentials.mcp_token_expires_at - now_ts).total_seconds()
        )

    view = await _upsert_notion_integration(
        access_token=access_token,
        refresh_token=token_response.get("refresh_token"),
        expires_in=token_response.get("expires_in"),
        mcp_access_token=existing_mcp_access_token,
        mcp_refresh_token=existing_mcp_refresh_token,
        mcp_expires_in=existing_mcp_expires_in,
        space_id=space_id,
        user_id=user_id,
        workspace_id=token_response.get("workspace_id"),
        workspace_name=token_response.get("workspace_name"),
        bot_id=token_response.get("bot_id"),
        event_store=event_store,
        clock=clock,
        logger=logger,
    )
    logger.debug(
        "Notion OAuth authorization code response keys: %s",
        list(token_response.keys()),
    )

    redirect_url = _build_return_url(
        config,
        return_path,
        {
            "status": "success",
            "spaceId": view.space_id,
            "processId": view.process_id,
            "workspaceId": view.workspace_id or "",
        },
    )
    if not view.has_mcp_token and config.mcp_client_id and config.mcp_client_secret:
        mcp_state = secrets.token_urlsafe(32)
        mcp_state_payload = {
            "space_id": space_id,
            "user_id": user_id or "unknown-user-id",
            "return_path": return_path,
        }
        redis_client.setex(
            _mcp_state_cache_key(mcp_state),
            config.state_ttl_seconds,
            json.dumps(mcp_state_payload),
        )

        authorize_params: dict[str, Any] = {
            "client_id": config.mcp_client_id,
            "response_type": "code",
            "redirect_uri": config.mcp_redirect_uri,
            "state": mcp_state,
        }
        if config.mcp_resource:
            authorize_params["resource"] = config.mcp_resource

        authorize_url = f"{config.mcp_authorize_endpoint}?{urlencode(authorize_params)}"
        logger.info(
            "Redirecting space %s to Notion MCP authorization (state=%s)",
            space_id,
            mcp_state,
        )
        return RedirectResponse(url=authorize_url, status_code=303)

    return RedirectResponse(url=redirect_url, status_code=303)


@router.get("/oauth/mcp/start", status_code=200)
async def start_notion_mcp_oauth_flow(
    user_id: Annotated[str, Depends(get_user_id_or_default)],
    redis_client: Annotated[Redis, Depends(get_redis_client)],
    event_store: Annotated[EventStore, Depends(get_event_store)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(lambda: get_logger("issue_solver.webapi.routers.notion.mcp.oauth")),
    ],
    space_id: str = Query(..., alias="space_id"),
    return_path: str | None = Query(None, alias="return_path"),
) -> dict[str, str]:
    if not space_id:
        raise HTTPException(
            status_code=400, detail="space_id is required to begin the Notion MCP flow."
        )

    integration = await get_notion_integration_event(event_store, space_id)
    if not integration:
        raise HTTPException(
            status_code=404,
            detail=(
                "No Notion integration is connected for this space. Connect Notion first "
                "before enabling MCP."
            ),
        )

    try:
        config = _get_oauth_config()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not config.mcp_client_id or not config.mcp_client_secret:
        raise HTTPException(
            status_code=503,
            detail=(
                "Notion MCP client credentials are not configured. Set NOTION_MCP_CLIENT_ID "
                "and NOTION_MCP_CLIENT_SECRET and retry."
            ),
        )

    normalized_return_path = _normalize_return_path(return_path)
    state = secrets.token_urlsafe(32)
    state_payload = {
        "space_id": space_id,
        "user_id": user_id or "unknown-user-id",
        "return_path": normalized_return_path,
    }
    redis_client.setex(
        _mcp_state_cache_key(state),
        config.state_ttl_seconds,
        json.dumps(state_payload),
    )

    authorize_params: dict[str, Any] = {
        "client_id": config.mcp_client_id,
        "response_type": "code",
        "redirect_uri": config.mcp_redirect_uri,
        "state": state,
    }
    if config.mcp_resource:
        authorize_params["resource"] = config.mcp_resource

    authorize_url = f"{config.mcp_authorize_endpoint}?{urlencode(authorize_params)}"
    logger.info(
        "Initiated Notion MCP OAuth flow for space %s (user=%s)", space_id, user_id
    )
    return {"authorizeUrl": authorize_url, "state": state}


@router.get("/oauth/mcp/callback")
async def handle_notion_mcp_oauth_callback(
    redis_client: Annotated[Redis, Depends(get_redis_client)],
    event_store: Annotated[EventStore, Depends(get_event_store)],
    clock: Annotated[Clock, Depends(get_clock)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(lambda: get_logger("issue_solver.webapi.routers.notion.mcp.oauth")),
    ],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    try:
        config = _get_oauth_config()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not state:
        raise HTTPException(status_code=400, detail="Missing OAuth state parameter.")

    cached_state_raw = redis_client.get(_mcp_state_cache_key(state))
    if cached_state_raw is None:
        raise HTTPException(
            status_code=400, detail="Unknown or expired Notion MCP OAuth state."
        )
    redis_client.delete(_mcp_state_cache_key(state))

    try:
        cached_state_bytes = (
            cached_state_raw
            if isinstance(cached_state_raw, (bytes, bytearray))
            else str(cached_state_raw).encode("utf-8")
        )
        state_payload = json.loads(cached_state_bytes.decode("utf-8"))
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=400, detail="Corrupted Notion MCP OAuth state payload."
        ) from exc

    space_id = state_payload.get("space_id")
    user_id = state_payload.get("user_id") or "unknown-user-id"
    return_path = state_payload.get("return_path") or DEFAULT_RETURN_PATH

    if not space_id:
        redirect_url = _build_return_url(
            config,
            return_path,
            {"status": "error", "error": "missing_space"},
        )
        return RedirectResponse(url=redirect_url, status_code=303)

    if error:
        redirect_url = _build_return_url(
            config,
            return_path,
            {"status": "error", "error": error},
        )
        return RedirectResponse(url=redirect_url, status_code=303)

    if not code:
        redirect_url = _build_return_url(
            config,
            return_path,
            {"status": "error", "error": "missing_code"},
        )
        return RedirectResponse(url=redirect_url, status_code=303)

    credentials = await get_notion_credentials(event_store, space_id)
    if not credentials:
        redirect_url = _build_return_url(
            config,
            return_path,
            {"status": "error", "error": "missing_integration"},
        )
        return RedirectResponse(url=redirect_url, status_code=303)

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": config.mcp_redirect_uri,
    }
    if config.mcp_resource:
        payload["resource"] = config.mcp_resource

    try:
        token_response = await _request_oauth_token(
            payload=payload,
            config=config,
            logger=logger,
            endpoint=config.mcp_token_endpoint,
            auth_method=config.mcp_token_auth_method,
            client_id_override=config.mcp_client_id,
            client_secret_override=config.mcp_client_secret,
            form_encode=True,
        )
    except HTTPException as exc:
        redirect_url = _build_return_url(
            config,
            return_path,
            {"status": "error", "error": str(exc.detail)},
        )
        return RedirectResponse(url=redirect_url, status_code=303)

    mcp_access_token = token_response.get("access_token")
    mcp_refresh_token = token_response.get("refresh_token")
    if not mcp_access_token or not mcp_refresh_token:
        logger.error(
            "Notion MCP token exchange response missing tokens: %s", token_response
        )
        redirect_url = _build_return_url(
            config,
            return_path,
            {"status": "error", "error": "invalid_mcp_token_response"},
        )
        return RedirectResponse(url=redirect_url, status_code=303)

    remaining_api_seconds: int | None = None
    if credentials.token_expires_at and credentials.token_expires_at > clock.now():
        remaining_api_seconds = int(
            (credentials.token_expires_at - clock.now()).total_seconds()
        )

    view = await _upsert_notion_integration(
        access_token=credentials.access_token,
        refresh_token=credentials.refresh_token,
        expires_in=remaining_api_seconds,
        mcp_access_token=mcp_access_token,
        mcp_refresh_token=mcp_refresh_token,
        mcp_expires_in=token_response.get("expires_in"),
        space_id=space_id,
        user_id=user_id,
        workspace_id=credentials.workspace_id,
        workspace_name=credentials.workspace_name,
        bot_id=credentials.bot_id,
        event_store=event_store,
        clock=clock,
        logger=logger,
    )

    redirect_url = _build_return_url(
        config,
        return_path,
        {
            "status": "success",
            "spaceId": view.space_id,
            "processId": view.process_id,
            "workspaceId": view.workspace_id or "",
            "mcp": "connected",
        },
    )
    return RedirectResponse(url=redirect_url, status_code=303)


@router.get("/mcp/oauth/callback")
async def handle_notion_mcp_oauth_callback_legacy(
    redis_client: Annotated[Redis, Depends(get_redis_client)],
    event_store: Annotated[EventStore, Depends(get_event_store)],
    clock: Annotated[Clock, Depends(get_clock)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(lambda: get_logger("issue_solver.webapi.routers.notion.mcp.oauth")),
    ],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    return await handle_notion_mcp_oauth_callback(
        redis_client=redis_client,
        event_store=event_store,
        clock=clock,
        logger=logger,
        code=code,
        state=state,
        error=error,
    )


def _normalize_return_path(return_path: str | None) -> str:
    if return_path is None or return_path.strip() == "":
        return DEFAULT_RETURN_PATH

    cleaned = return_path.strip()
    parsed = urlparse(cleaned)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        raise HTTPException(
            status_code=400,
            detail="Unsupported scheme for return_path.",
        )
    if not parsed.scheme and not cleaned.startswith("/"):
        raise HTTPException(
            status_code=400,
            detail="return_path must be an absolute path or a fully qualified URL.",
        )
    return cleaned


def _state_cache_key(state: str) -> str:
    return f"{OAUTH_STATE_CACHE_PREFIX}{state}"


def _mcp_state_cache_key(state: str) -> str:
    return f"{MCP_OAUTH_STATE_CACHE_PREFIX}{state}"


def _derive_mcp_redirect_uri(redirect_uri: str) -> str:
    parsed = urlparse(redirect_uri)
    if not parsed.scheme or not parsed.netloc:
        raise RuntimeError(
            "NOTION_OAUTH_REDIRECT_URI must be an absolute URL to derive the MCP redirect URI."
        )

    parsed_parts = list(parsed)
    parsed_parts[2] = MCP_DEFAULT_REDIRECT_PATH
    parsed_parts[3] = ""
    parsed_parts[4] = ""
    return urlunparse(parsed_parts)


def _get_mcp_auth_server_metadata() -> dict[str, Any]:
    global _MCP_AUTH_SERVER_METADATA
    if _MCP_AUTH_SERVER_METADATA is not None:
        return _MCP_AUTH_SERVER_METADATA

    try:
        response = httpx.get(
            NOTION_MCP_AUTH_SERVER_METADATA_URL,
            timeout=10.0,
            headers={"Accept": "application/json"},
        )
    except httpx.RequestError as exc:  # pragma: no cover - network failure
        module_logger.warning("Unable to fetch Notion MCP OAuth metadata: %s", exc)
        _MCP_AUTH_SERVER_METADATA = {}
        return _MCP_AUTH_SERVER_METADATA

    if not response.is_success:  # pragma: no cover - unexpected HTTP status
        module_logger.warning(
            "Notion MCP metadata endpoint returned %s: %s",
            response.status_code,
            response.text,
        )
        _MCP_AUTH_SERVER_METADATA = {}
        return _MCP_AUTH_SERVER_METADATA

    try:
        _MCP_AUTH_SERVER_METADATA = response.json()
    except ValueError as exc:  # pragma: no cover - invalid JSON
        module_logger.warning("Invalid JSON from Notion MCP metadata endpoint: %s", exc)
        _MCP_AUTH_SERVER_METADATA = {}
    return _MCP_AUTH_SERVER_METADATA


def _register_mcp_client(
    *,
    registration_endpoint: str,
    redirect_uri: str,
    client_name: str,
    default_auth_method: str,
) -> tuple[str, str, str]:
    payload: dict[str, Any] = {
        "client_name": client_name,
        "redirect_uris": [redirect_uri],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": default_auth_method,
    }

    try:
        response = httpx.post(
            registration_endpoint,
            json=payload,
            timeout=10.0,
            headers={"Content-Type": "application/json"},
        )
    except httpx.RequestError as exc:  # pragma: no cover - network failure
        module_logger.error("Failed to register Notion MCP client: %s", exc)
        raise RuntimeError(
            "Unable to register Notion MCP client with the authorization server."
        ) from exc

    if response.status_code not in (200, 201):  # pragma: no cover - unexpected
        module_logger.error(
            "Notion MCP registration failed (%s): %s",
            response.status_code,
            response.text,
        )
        raise RuntimeError("Notion MCP registration endpoint rejected the request.")

    try:
        body = response.json()
    except ValueError as exc:  # pragma: no cover - invalid JSON
        module_logger.error("Invalid JSON from MCP registration endpoint: %s", exc)
        raise RuntimeError(
            "Received invalid payload from Notion MCP registration."
        ) from exc

    client_id = body.get("client_id")
    client_secret = body.get("client_secret")
    auth_method = body.get("token_endpoint_auth_method") or default_auth_method

    if not isinstance(client_id, str) or not isinstance(client_secret, str):
        module_logger.error("MCP registration returned unexpected payload: %s", body)
        raise RuntimeError("Notion MCP registration did not return client credentials.")

    module_logger.info("Registered Notion MCP client via %s", registration_endpoint)
    return client_id, client_secret, auth_method


def _get_oauth_config() -> NotionOAuthConfig:
    global _OAUTH_CONFIG
    if _OAUTH_CONFIG is not None:
        return _OAUTH_CONFIG

    client_id = os.environ.get("NOTION_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("NOTION_OAUTH_CLIENT_SECRET")
    redirect_uri = os.environ.get("NOTION_OAUTH_REDIRECT_URI")
    return_base_url = os.environ.get("NOTION_OAUTH_RETURN_BASE_URL")
    state_ttl = int(os.environ.get("NOTION_OAUTH_STATE_TTL_SECONDS", "600"))
    mcp_metadata = _get_mcp_auth_server_metadata()
    default_mcp_token_endpoint = mcp_metadata.get(
        "token_endpoint", "https://mcp.notion.com/token"
    )
    default_mcp_authorize_endpoint = mcp_metadata.get(
        "authorization_endpoint", "https://mcp.notion.com/authorize"
    )
    default_mcp_registration_endpoint = mcp_metadata.get("registration_endpoint")

    mcp_client_id = os.environ.get("NOTION_MCP_CLIENT_ID")
    mcp_client_secret = os.environ.get("NOTION_MCP_CLIENT_SECRET")
    mcp_token_endpoint = os.environ.get(
        "NOTION_MCP_TOKEN_ENDPOINT", default_mcp_token_endpoint
    )
    mcp_scope = os.environ.get("NOTION_MCP_TOKEN_SCOPE")
    mcp_token_auth_method = os.environ.get(
        "NOTION_MCP_TOKEN_AUTH_METHOD", "client_secret_basic"
    )
    mcp_registration_endpoint = (
        os.environ.get(
            "NOTION_MCP_REGISTRATION_ENDPOINT", default_mcp_registration_endpoint or ""
        )
        or None
    )
    mcp_client_name = os.environ.get("NOTION_MCP_CLIENT_NAME", "Issue Solver MCP")
    mcp_authorize_endpoint = os.environ.get(
        "NOTION_MCP_AUTHORIZE_ENDPOINT", default_mcp_authorize_endpoint
    )
    api_resource = os.environ.get("NOTION_API_RESOURCE", NOTION_API_RESOURCE)
    mcp_resource = os.environ.get("NOTION_MCP_RESOURCE", NOTION_MCP_RESOURCE)

    if not client_id or not client_secret or not redirect_uri:
        raise RuntimeError(
            "Notion OAuth is not configured. Set NOTION_OAUTH_CLIENT_ID, "
            "NOTION_OAUTH_CLIENT_SECRET, and NOTION_OAUTH_REDIRECT_URI."
        )

    # Derive mcp_redirect_uri after validating redirect_uri is not None
    mcp_redirect_uri = os.environ.get("NOTION_MCP_OAUTH_REDIRECT_URI")
    if not mcp_redirect_uri:
        mcp_redirect_uri = _derive_mcp_redirect_uri(redirect_uri)

    needs_mcp_registration = not mcp_client_id or not mcp_client_secret
    if not needs_mcp_registration and (
        mcp_client_id == client_id or mcp_client_secret == client_secret
    ):
        module_logger.warning(
            "Provided MCP credentials match the standard Notion OAuth client; dynamic registration will run instead."
        )
        needs_mcp_registration = True

    if needs_mcp_registration:
        if not mcp_registration_endpoint:
            raise RuntimeError(
                "Notion MCP client credentials are missing and automatic registration "
                "is unavailable. Set NOTION_MCP_CLIENT_ID and NOTION_MCP_CLIENT_SECRET."
            )

        try:
            registered_id, registered_secret, registered_auth_method = (
                _register_mcp_client(
                    registration_endpoint=mcp_registration_endpoint,
                    redirect_uri=mcp_redirect_uri,
                    client_name=mcp_client_name,
                    default_auth_method=mcp_token_auth_method,
                )
            )
        except RuntimeError as exc:  # pragma: no cover - network issue at startup
            raise RuntimeError(
                "Failed to register Notion MCP client automatically; set "
                "NOTION_MCP_CLIENT_ID and NOTION_MCP_CLIENT_SECRET manually."
            ) from exc

        mcp_client_id = registered_id
        mcp_client_secret = registered_secret
        mcp_token_auth_method = registered_auth_method or mcp_token_auth_method

        os.environ["NOTION_MCP_CLIENT_ID"] = mcp_client_id
        os.environ["NOTION_MCP_CLIENT_SECRET"] = mcp_client_secret
        os.environ["NOTION_MCP_TOKEN_AUTH_METHOD"] = mcp_token_auth_method
        module_logger.info(
            "Configured Notion MCP client via dynamic registration (client_id=%s)",
            mcp_client_id,
        )
        module_logger.warning(
            "Store the generated Notion MCP credentials securely and set them in the environment "
            "for future runs (client_id=%s, client_secret=%s)",
            mcp_client_id,
            mcp_client_secret,
        )

    _OAUTH_CONFIG = NotionOAuthConfig(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        return_base_url=return_base_url,
        state_ttl_seconds=state_ttl,
        mcp_client_id=mcp_client_id,
        mcp_client_secret=mcp_client_secret,
        mcp_token_endpoint=mcp_token_endpoint,
        mcp_scope=mcp_scope,
        mcp_token_auth_method=mcp_token_auth_method,
        api_resource=api_resource,
        mcp_resource=mcp_resource,
        mcp_registration_endpoint=mcp_registration_endpoint,
        mcp_client_name=mcp_client_name,
        mcp_authorize_endpoint=mcp_authorize_endpoint,
        mcp_redirect_uri=mcp_redirect_uri,
    )
    return _OAUTH_CONFIG


def _build_return_url(
    config: NotionOAuthConfig,
    target: str,
    params: dict[str, str],
) -> str:
    destination = target
    parsed = urlparse(destination)
    if not parsed.scheme and config.return_base_url:
        destination = urljoin(
            config.return_base_url.rstrip("/") + "/", destination.lstrip("/")
        )
        parsed = urlparse(destination)

    parsed_parts = list(parsed)
    query_params = dict(parse_qsl(parsed_parts[4]))
    for key, value in params.items():
        if value is not None:
            query_params[key] = value
    parsed_parts[4] = urlencode(query_params)
    return urlunparse(parsed_parts)


async def _exchange_authorization_code(
    *,
    config: NotionOAuthConfig,
    code: str,
    logger: logging.Logger | logging.LoggerAdapter,
) -> dict[str, Any]:
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": config.redirect_uri,
    }
    if config.api_resource:
        payload["resource"] = config.api_resource
    return await _request_oauth_token(payload=payload, config=config, logger=logger)


async def _refresh_access_token(
    *,
    config: NotionOAuthConfig,
    refresh_token: str,
    logger: logging.Logger | logging.LoggerAdapter,
) -> dict[str, Any]:
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    if config.api_resource:
        payload["resource"] = config.api_resource
    return await _request_oauth_token(payload=payload, config=config, logger=logger)


async def _exchange_for_mcp_token(
    *,
    config: NotionOAuthConfig,
    credentials: NotionCredentials,
    logger: logging.Logger | logging.LoggerAdapter,
) -> dict[str, Any]:
    client_id = config.mcp_client_id
    client_secret = config.mcp_client_secret
    auth_method = config.mcp_token_auth_method

    if not client_id or not client_secret:
        logger.error(
            "Notion MCP client credentials are not configured. Set NOTION_MCP_CLIENT_ID and NOTION_MCP_CLIENT_SECRET."
        )
        raise HTTPException(
            status_code=503,
            detail=(
                "Notion MCP client credentials are missing. Configure NOTION_MCP_CLIENT_ID and NOTION_MCP_CLIENT_SECRET."
            ),
        )

    if not credentials.mcp_refresh_token:
        logger.error(
            "Cannot request MCP token without an MCP refresh token (space=%s)",
            credentials.process_id,
        )
        raise HTTPException(
            status_code=503,
            detail=(
                "Notion MCP token exchange requires completing the Notion MCP OAuth flow. "
                "Reconnect Notion MCP from the integrations page to generate one."
            ),
        )

    payload: dict[str, Any] = {
        "grant_type": "refresh_token",
        "refresh_token": credentials.mcp_refresh_token,
    }
    if config.mcp_scope:
        payload["scope"] = config.mcp_scope
    if config.mcp_resource:
        payload["resource"] = config.mcp_resource

    logger.debug("Requesting Notion MCP token via %s", config.mcp_token_endpoint)

    return await _request_oauth_token(
        payload=payload,
        config=config,
        logger=logger,
        endpoint=config.mcp_token_endpoint,
        auth_method=auth_method,
        client_id_override=client_id,
        client_secret_override=client_secret,
        form_encode=True,
    )


async def get_mcp_access_token(
    *,
    credentials: NotionCredentials,
    logger: logging.Logger | logging.LoggerAdapter,
) -> str:
    if not credentials.mcp_refresh_token:
        logger.warning(
            "Space %s is missing Notion MCP OAuth credentials. Prompting user to reconnect MCP.",
            credentials.process_id,
        )
        raise HTTPException(
            status_code=401,
            detail=(
                "Notion MCP is not connected for this space. Reconnect Notion MCP to continue."
            ),
        )
    try:
        config = _get_oauth_config()
    except RuntimeError as exc:  # pragma: no cover - configuration error
        logger.error("Notion MCP token exchange requires OAuth config: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Notion OAuth is not configured for MCP token exchange.",
        ) from exc

    try:
        exchange_response = await _exchange_for_mcp_token(
            config=config,
            credentials=credentials,
            logger=logger,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected error exchanging Notion MCP token: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Failed to exchange Notion MCP token. Try reconnecting Notion.",
        ) from exc

    mcp_access_token = exchange_response.get("access_token")
    if not isinstance(mcp_access_token, str) or not mcp_access_token.strip():
        logger.error(
            "Notion MCP token exchange response missing access_token: %s",
            exchange_response,
        )
        raise HTTPException(
            status_code=502,
            detail="Notion MCP token exchange returned an invalid response.",
        )

    logger.debug(
        "Received Notion MCP token (len=%d)",
        len(mcp_access_token),
    )
    return mcp_access_token


async def _request_oauth_token(
    *,
    payload: dict[str, Any],
    config: NotionOAuthConfig,
    logger: logging.Logger | logging.LoggerAdapter,
    endpoint: str | None = None,
    auth_method: str = "client_secret_basic",
    client_id_override: str | None = None,
    client_secret_override: str | None = None,
    form_encode: bool = False,
) -> dict[str, Any]:
    target = endpoint or NOTION_OAUTH_TOKEN_URL
    headers = {
        "Content-Type": (
            "application/x-www-form-urlencoded" if form_encode else "application/json"
        )
    }
    request_payload = {
        key: value for key, value in payload.items() if value is not None
    }

    if auth_method == "client_secret_basic":
        auth = base64.b64encode(
            f"{(client_id_override or config.client_id)}:{(client_secret_override or config.client_secret)}".encode(
                "utf-8"
            )
        ).decode("utf-8")
        headers["Authorization"] = f"Basic {auth}"
    elif auth_method == "client_secret_post":
        request_payload["client_id"] = client_id_override or config.client_id
        request_payload["client_secret"] = (
            client_secret_override or config.client_secret
        )
    else:  # pragma: no cover - unexpected
        logger.error("Unsupported OAuth client auth method: %s", auth_method)
        raise HTTPException(
            status_code=503,
            detail="Unsupported OAuth client authentication method for Notion token exchange.",
        )

    async with httpx.AsyncClient(timeout=10.0) as client:
        if form_encode:
            form_payload: dict[str, str] = {}
            for key, value in request_payload.items():
                if isinstance(value, (list, tuple)):
                    form_payload[key] = " ".join(str(item) for item in value)
                else:
                    form_payload[key] = str(value)
            response = await client.post(target, data=form_payload, headers=headers)
        else:
            response = await client.post(target, json=request_payload, headers=headers)

    if response.status_code == 400:
        try:
            detail = response.json()
        except Exception:  # pragma: no cover - defensive
            detail = response.text
        logger.warning("Notion OAuth returned 400: %s", detail)
        raise HTTPException(
            status_code=400,
            detail="Notion rejected the OAuth request. Reconnect the integration.",
        )

    if not response.is_success:
        logger.error(
            "Unexpected Notion OAuth error %s: %s",
            response.status_code,
            response.text,
        )
        raise HTTPException(
            status_code=502,
            detail="Failed to exchange tokens with Notion OAuth service.",
        )

    return response.json()


async def ensure_fresh_notion_credentials(
    *,
    event_store: EventStore,
    credentials: NotionCredentials,
    space_id: str,
    user_id: str,
    clock: Clock,
    logger: logging.Logger | logging.LoggerAdapter,
) -> NotionCredentials:
    # If there is no refresh token (some OAuth tokens are long-lived), allow usage.
    if not credentials.refresh_token:
        return credentials

    # Provide a small buffer (60 seconds) before attempting a refresh.
    now = clock.now()
    if credentials.token_expires_at and credentials.token_expires_at > now + timedelta(
        seconds=60
    ):
        return credentials

    try:
        config = _get_oauth_config()
    except RuntimeError as exc:
        logger.warning("Cannot refresh Notion tokens for space %s: %s", space_id, exc)
        raise HTTPException(
            status_code=401,
            detail="Notion credentials expired. Reconnect Notion to continue.",
        ) from exc

    try:
        token_response = await _refresh_access_token(
            config=config,
            refresh_token=credentials.refresh_token,
            logger=logger,
        )
        logger.debug(
            "Notion OAuth refresh response keys: %s",
            list(token_response.keys()),
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected error refreshing Notion token: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Failed to refresh Notion credentials. Try reconnecting.",
        ) from exc

    new_access_token = token_response.get("access_token")
    if not new_access_token:
        logger.error(
            "Notion refresh response missing access_token for space %s", space_id
        )
        raise HTTPException(
            status_code=502,
            detail="Notion returned an invalid refresh response.",
        )

    mcp_expires_in: int | None = None
    now_ts = clock.now()
    if credentials.mcp_token_expires_at and credentials.mcp_token_expires_at > now_ts:
        mcp_expires_in = max(
            0,
            int((credentials.mcp_token_expires_at - now_ts).total_seconds()),
        )

    updated_view = await _upsert_notion_integration(
        access_token=new_access_token,
        refresh_token=token_response.get("refresh_token", credentials.refresh_token),
        expires_in=token_response.get("expires_in"),
        mcp_access_token=credentials.mcp_access_token,
        mcp_refresh_token=credentials.mcp_refresh_token,
        mcp_expires_in=mcp_expires_in,
        space_id=space_id,
        user_id=user_id,
        workspace_id=token_response.get("workspace_id") or credentials.workspace_id,
        workspace_name=token_response.get("workspace_name")
        or credentials.workspace_name,
        bot_id=token_response.get("bot_id") or credentials.bot_id,
        event_store=event_store,
        clock=clock,
        logger=logger,
    )

    refreshed = await get_notion_credentials(event_store, space_id)
    if not refreshed:
        raise HTTPException(
            status_code=500,
            detail="Failed to update Notion credentials after refresh.",
        )

    logger.info(
        "Refreshed Notion credentials for space %s (process=%s)",
        space_id,
        updated_view.process_id,
    )
    return refreshed
