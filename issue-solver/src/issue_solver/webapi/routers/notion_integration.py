import base64
import json
import logging
import os
import secrets
import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Annotated, Any, Literal
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
NOTION_MCP_VERSION = "2022-06-28"

router = APIRouter(prefix="/integrations/notion", tags=["notion-integrations"])

NOTION_OAUTH_AUTHORIZE_URL = f"{NOTION_API_BASE_URL}/oauth/authorize"
NOTION_OAUTH_TOKEN_URL = f"{NOTION_API_BASE_URL}/oauth/token"
OAUTH_STATE_CACHE_PREFIX = "notion:oauth:state:"
DEFAULT_RETURN_PATH = "/integrations/notion/callback"


@dataclass(frozen=True)
class NotionOAuthConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    return_base_url: str | None
    state_ttl_seconds: int
    mcp_audience: str
    mcp_requested_token_type: str
    mcp_scope: str | None


_OAUTH_CONFIG: NotionOAuthConfig | None = None


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
    space_id: str,
    user_id: str,
    workspace_id: str | None,
    workspace_name: str | None,
    bot_id: str | None,
    event_store: EventStore,
    clock: Clock,
    logger: logging.Logger | logging.LoggerAdapter,
    auth_mode: Literal["manual", "oauth"],
) -> NotionIntegrationView:
    integration = await get_notion_integration_event(event_store, space_id)
    now = clock.now()
    token_expires_at = (
        now + timedelta(seconds=expires_in) if expires_in is not None else None
    )

    resolved_workspace_id = workspace_id
    resolved_workspace_name = workspace_name
    resolved_bot_id = bot_id
    resolved_auth_mode = auth_mode

    if integration:
        resolved_workspace_id = resolved_workspace_id or integration.workspace_id
        resolved_workspace_name = resolved_workspace_name or integration.workspace_name
        resolved_bot_id = resolved_bot_id or integration.bot_id
        resolved_auth_mode = (
            auth_mode if auth_mode != integration.auth_mode else integration.auth_mode
        )

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
            auth_mode=resolved_auth_mode,
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
            auth_mode=resolved_auth_mode,
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
        space_id=request.space_id,
        user_id=user_id,
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        bot_id=bot_id,
        event_store=event_store,
        clock=clock,
        logger=logger,
        auth_mode="manual",
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

    return await _upsert_notion_integration(
        access_token=request.access_token,
        refresh_token=None,
        expires_in=None,
        space_id=space_id,
        user_id=user_id,
        workspace_id=workspace_id or integration.workspace_id,
        workspace_name=workspace_name or integration.workspace_name,
        bot_id=bot_id or integration.bot_id,
        event_store=event_store,
        clock=clock,
        logger=logger,
        auth_mode=integration.auth_mode,
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

    return NotionIntegrationView(
        space_id=space_id,
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        bot_id=bot_id,
        connected_at=integration.occurred_at,
        process_id=integration.process_id,
        token_expires_at=token_expires_at,
        has_valid_token=credentials is not None,
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

    authorize_params = {
        "client_id": config.client_id,
        "response_type": "code",
        "owner": "user",
        "redirect_uri": config.redirect_uri,
        "state": state,
    }
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

    view = await _upsert_notion_integration(
        access_token=access_token,
        refresh_token=token_response.get("refresh_token"),
        expires_in=token_response.get("expires_in"),
        space_id=space_id,
        user_id=user_id,
        workspace_id=token_response.get("workspace_id"),
        workspace_name=token_response.get("workspace_name"),
        bot_id=token_response.get("bot_id"),
        event_store=event_store,
        clock=clock,
        logger=logger,
        auth_mode="oauth",
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
    return RedirectResponse(url=redirect_url, status_code=303)


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


def _get_oauth_config() -> NotionOAuthConfig:
    global _OAUTH_CONFIG
    if _OAUTH_CONFIG is not None:
        return _OAUTH_CONFIG

    client_id = os.environ.get("NOTION_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("NOTION_OAUTH_CLIENT_SECRET")
    redirect_uri = os.environ.get("NOTION_OAUTH_REDIRECT_URI")
    return_base_url = os.environ.get("NOTION_OAUTH_RETURN_BASE_URL")
    state_ttl = int(os.environ.get("NOTION_OAUTH_STATE_TTL_SECONDS", "600"))
    mcp_audience = os.environ.get(
        "NOTION_MCP_TOKEN_AUDIENCE", "https://mcp.notion.com/mcp"
    )
    mcp_requested_token_type = os.environ.get(
        "NOTION_MCP_REQUESTED_TOKEN_TYPE", "urn:ietf:params:oauth:token-type:jwt"
    )
    mcp_scope = os.environ.get("NOTION_MCP_TOKEN_SCOPE")

    if not client_id or not client_secret or not redirect_uri:
        raise RuntimeError(
            "Notion OAuth is not configured. Set NOTION_OAUTH_CLIENT_ID, "
            "NOTION_OAUTH_CLIENT_SECRET, and NOTION_OAUTH_REDIRECT_URI."
        )

    _OAUTH_CONFIG = NotionOAuthConfig(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        return_base_url=return_base_url,
        state_ttl_seconds=state_ttl,
        mcp_audience=mcp_audience,
        mcp_requested_token_type=mcp_requested_token_type,
        mcp_scope=mcp_scope,
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
    return await _request_oauth_token(payload=payload, config=config, logger=logger)


async def _exchange_for_mcp_token(
    *,
    config: NotionOAuthConfig,
    access_token: str,
    logger: logging.Logger | logging.LoggerAdapter,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "subject_token": access_token,
        "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "requested_token_type": config.mcp_requested_token_type,
        "audience": config.mcp_audience,
    }
    if config.mcp_scope:
        payload["scope"] = config.mcp_scope
    return await _request_oauth_token(payload=payload, config=config, logger=logger)


async def get_mcp_access_token(
    *,
    access_token: str,
    logger: logging.Logger | logging.LoggerAdapter,
) -> str:
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
            access_token=access_token,
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
        "Received Notion MCP token (len=%d, requested_token_type=%s)",
        len(mcp_access_token),
        config.mcp_requested_token_type,
    )
    return mcp_access_token


async def _request_oauth_token(
    *,
    payload: dict[str, Any],
    config: NotionOAuthConfig,
    logger: logging.Logger | logging.LoggerAdapter,
) -> dict[str, Any]:
    auth = base64.b64encode(
        f"{config.client_id}:{config.client_secret}".encode("utf-8")
    ).decode("utf-8")
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            NOTION_OAUTH_TOKEN_URL, json=payload, headers=headers
        )

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
    if credentials.auth_mode != "oauth":
        logger.warning(
            "Notion MCP requires OAuth-connected credentials; space %s is using %s mode",
            space_id,
            credentials.auth_mode,
        )
        raise HTTPException(
            status_code=401,
            detail=(
                "Notion MCP requires an OAuth-connected integration. "
                "Reconnect Notion from the integrations page to continue."
            ),
        )

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

    updated_view = await _upsert_notion_integration(
        access_token=new_access_token,
        refresh_token=token_response.get("refresh_token", credentials.refresh_token),
        expires_in=token_response.get("expires_in"),
        space_id=space_id,
        user_id=user_id,
        workspace_id=token_response.get("workspace_id") or credentials.workspace_id,
        workspace_name=token_response.get("workspace_name")
        or credentials.workspace_name,
        bot_id=token_response.get("bot_id") or credentials.bot_id,
        event_store=event_store,
        clock=clock,
        logger=logger,
        auth_mode=credentials.auth_mode,
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
