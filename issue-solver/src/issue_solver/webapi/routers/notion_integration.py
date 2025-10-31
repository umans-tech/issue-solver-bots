from __future__ import annotations

import base64
import json
import os
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Annotated, Any
from urllib.parse import urlencode, urljoin, urlparse

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
from issue_solver.webapi.payloads import NotionIntegrationView

NOTION_MCP_RESOURCE = "https://mcp.notion.com"
NOTION_VERSION = "2022-06-28"
DEFAULT_RETURN_PATH = "/integrations/notion/callback"
MCP_OAUTH_STATE_CACHE_PREFIX = "notion:mcp:oauth:state:"

router = APIRouter(prefix="/integrations/notion", tags=["notion-integrations"])


@dataclass(frozen=True)
class NotionMcpSettings:
    client_id: str
    client_secret: str
    redirect_uri: str
    authorize_endpoint: str
    token_endpoint: str
    token_auth_method: str
    scope: str | None
    state_ttl_seconds: int
    return_base_url: str | None


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required but was not provided.")
    return value


@lru_cache(maxsize=1)
def _get_mcp_settings() -> NotionMcpSettings:
    state_ttl = int(os.environ.get("NOTION_MCP_STATE_TTL_SECONDS", "600"))
    return NotionMcpSettings(
        client_id=_require_env("NOTION_MCP_CLIENT_ID"),
        client_secret=_require_env("NOTION_MCP_CLIENT_SECRET"),
        redirect_uri=os.environ.get(
            "NOTION_MCP_OAUTH_REDIRECT_URI",
            "http://localhost:8000/integrations/notion/mcp/oauth/callback",
        ),
        authorize_endpoint=os.environ.get(
            "NOTION_MCP_AUTHORIZE_ENDPOINT",
            "https://mcp.notion.com/authorize",
        ),
        token_endpoint=os.environ.get(
            "NOTION_MCP_TOKEN_ENDPOINT",
            "https://mcp.notion.com/token",
        ),
        token_auth_method=os.environ.get(
            "NOTION_MCP_TOKEN_AUTH_METHOD",
            "client_secret_basic",
        ),
        scope=os.environ.get("NOTION_MCP_TOKEN_SCOPE"),
        state_ttl_seconds=state_ttl,
        return_base_url=(
            os.environ.get("NOTION_MCP_RETURN_BASE_URL")
            or os.environ.get("NOTION_OAUTH_RETURN_BASE_URL")
        ),
    )


def _seconds_left(timestamp: datetime | None, clock: Clock) -> int | None:
    if not timestamp:
        return None
    remaining = int((timestamp - clock.now()).total_seconds())
    return max(0, remaining)


async def _upsert_notion_integration(
    *,
    space_id: str,
    user_id: str,
    event_store: EventStore,
    clock: Clock,
    logger: Any,
    mcp_access_token: str | None,
    mcp_refresh_token: str | None,
    mcp_expires_in: int | None,
    workspace_id: str | None = None,
    workspace_name: str | None = None,
    bot_id: str | None = None,
    access_token: str | None = None,
    refresh_token: str | None = None,
    token_expires_in: int | None = None,
) -> NotionIntegrationView:
    integration = await get_notion_integration_event(event_store, space_id)
    now = clock.now()

    token_expires_at = (
        now + timedelta(seconds=token_expires_in) if token_expires_in else None
    )
    mcp_token_expires_at = (
        now + timedelta(seconds=mcp_expires_in) if mcp_expires_in else None
    )

    resolved_workspace_id = workspace_id
    resolved_workspace_name = workspace_name
    resolved_bot_id = bot_id

    if integration:
        resolved_workspace_id = resolved_workspace_id or integration.workspace_id
        resolved_workspace_name = resolved_workspace_name or integration.workspace_name
        resolved_bot_id = resolved_bot_id or integration.bot_id

        rotation = NotionIntegrationTokenRotated(
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
            new_mcp_access_token=mcp_access_token,
            new_mcp_refresh_token=mcp_refresh_token,
            mcp_token_expires_at=mcp_token_expires_at,
        )
        await event_store.append(integration.process_id, rotation)
        process_id = integration.process_id
        connected_at = integration.occurred_at
    else:
        process_id = str(uuid.uuid4())
        connected = NotionIntegrationConnected(
            occurred_at=now,
            user_id=user_id,
            space_id=space_id,
            process_id=process_id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            workspace_id=resolved_workspace_id,
            workspace_name=resolved_workspace_name,
            bot_id=resolved_bot_id,
            mcp_access_token=mcp_access_token,
            mcp_refresh_token=mcp_refresh_token,
            mcp_token_expires_at=mcp_token_expires_at,
        )
        await event_store.append(process_id, connected)
        connected_at = now
        logger.info(
            "Notion MCP integration created for space %s (process=%s)",
            space_id,
            process_id,
        )

    credentials = await get_notion_credentials(event_store, space_id)
    has_mcp_token = bool(credentials and credentials.mcp_refresh_token)
    has_valid_token = bool(credentials and credentials.access_token)

    if credentials:
        resolved_workspace_id = credentials.workspace_id or resolved_workspace_id
        resolved_workspace_name = credentials.workspace_name or resolved_workspace_name
        resolved_bot_id = credentials.bot_id or resolved_bot_id
        token_expires_at = credentials.token_expires_at or token_expires_at

    return NotionIntegrationView(
        space_id=space_id,
        process_id=credentials.process_id if credentials else process_id,
        connected_at=connected_at,
        workspace_id=resolved_workspace_id,
        workspace_name=resolved_workspace_name,
        bot_id=resolved_bot_id,
        token_expires_at=token_expires_at,
        has_valid_token=has_valid_token,
        has_mcp_token=has_mcp_token,
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
    has_valid_token = bool(credentials and credentials.access_token)
    has_mcp_token = bool(credentials and credentials.mcp_refresh_token)
    workspace_id = credentials.workspace_id if credentials else integration.workspace_id
    workspace_name = (
        credentials.workspace_name if credentials else integration.workspace_name
    )
    bot_id = credentials.bot_id if credentials else integration.bot_id
    token_expires_at = credentials.token_expires_at if credentials else None

    return NotionIntegrationView(
        space_id=space_id,
        process_id=integration.process_id,
        connected_at=integration.occurred_at,
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        bot_id=bot_id,
        token_expires_at=token_expires_at,
        has_valid_token=has_valid_token,
        has_mcp_token=has_mcp_token,
    )


@router.get("/oauth/mcp/start", status_code=200)
async def start_notion_mcp_oauth_flow(
    user_id: Annotated[str, Depends(get_user_id_or_default)],
    redis_client: Annotated[Redis, Depends(get_redis_client)],
    logger: Annotated[
        Any,
        Depends(lambda: get_logger("issue_solver.webapi.routers.notion.mcp.oauth")),
    ],
    space_id: str = Query(..., alias="space_id"),
    return_path: str | None = Query(None, alias="return_path"),
) -> dict[str, str]:
    if not space_id:
        raise HTTPException(
            status_code=400,
            detail="space_id is required to begin the Notion MCP flow.",
        )

    try:
        settings = _get_mcp_settings()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    normalized_return_path = _normalize_return_path(return_path)
    state_payload = {
        "space_id": space_id,
        "user_id": user_id or "unknown-user-id",
        "return_path": normalized_return_path,
    }

    state, authorize_url = _initiate_oauth_flow(
        authorize_endpoint=settings.authorize_endpoint,
        base_params={
            "client_id": settings.client_id,
            "response_type": "code",
            "redirect_uri": settings.redirect_uri,
            "resource": NOTION_MCP_RESOURCE,
        },
        redis_client=redis_client,
        state_ttl_seconds=settings.state_ttl_seconds,
        state_cache_prefix=MCP_OAUTH_STATE_CACHE_PREFIX,
        state_payload=state_payload,
    )

    logger.info(
        "Initiated Notion MCP OAuth flow for space %s (user=%s)",
        space_id,
        user_id,
    )
    return {"authorizeUrl": authorize_url, "state": state}


@router.get("/mcp/oauth/callback")
async def handle_notion_mcp_oauth_callback(
    redis_client: Annotated[Redis, Depends(get_redis_client)],
    event_store: Annotated[EventStore, Depends(get_event_store)],
    clock: Annotated[Clock, Depends(get_clock)],
    logger: Annotated[
        Any,
        Depends(lambda: get_logger("issue_solver.webapi.routers.notion.mcp.oauth")),
    ],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    try:
        settings = _get_mcp_settings()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    state_payload = _read_oauth_state(
        redis_client=redis_client,
        state_cache_prefix=MCP_OAUTH_STATE_CACHE_PREFIX,
        state=state,
        missing_detail="Missing OAuth state parameter.",
    )

    space_id = state_payload.get("space_id")
    user_id = state_payload.get("user_id") or "unknown-user-id"
    return_path = state_payload.get("return_path") or DEFAULT_RETURN_PATH

    if not space_id:
        redirect_url = _build_return_url(
            base_url=settings.return_base_url,
            target=return_path,
            params={"status": "error", "error": "missing_space"},
        )
        return RedirectResponse(url=redirect_url, status_code=303)

    if error:
        redirect_url = _build_return_url(
            base_url=settings.return_base_url,
            target=return_path,
            params={"status": "error", "error": error},
        )
        return RedirectResponse(url=redirect_url, status_code=303)

    if not code:
        redirect_url = _build_return_url(
            base_url=settings.return_base_url,
            target=return_path,
            params={"status": "error", "error": "missing_code"},
        )
        return RedirectResponse(url=redirect_url, status_code=303)

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.redirect_uri,
        "resource": NOTION_MCP_RESOURCE,
    }
    if settings.scope:
        payload["scope"] = settings.scope

    try:
        token_response = await _request_oauth_token(
            payload=payload,
            logger=logger,
            endpoint=settings.token_endpoint,
            client_id=settings.client_id,
            client_secret=settings.client_secret,
            auth_method=settings.token_auth_method,
            form_encode=True,
        )
    except HTTPException as exc:
        redirect_url = _build_return_url(
            base_url=settings.return_base_url,
            target=return_path,
            params={"status": "error", "error": str(exc.detail)},
        )
        return RedirectResponse(url=redirect_url, status_code=303)

    mcp_access_token = token_response.get("access_token")
    mcp_refresh_token = token_response.get("refresh_token")
    if not mcp_access_token or not mcp_refresh_token:
        logger.error(
            "Notion MCP token exchange response missing tokens: %s",
            token_response,
        )
        redirect_url = _build_return_url(
            base_url=settings.return_base_url,
            target=return_path,
            params={"status": "error", "error": "invalid_mcp_token_response"},
        )
        return RedirectResponse(url=redirect_url, status_code=303)

    workspace_id = token_response.get("workspace_id")
    workspace_name = token_response.get("workspace_name")
    bot_id = token_response.get("bot_id")

    view = await _upsert_notion_integration(
        space_id=space_id,
        user_id=user_id,
        event_store=event_store,
        clock=clock,
        logger=logger,
        mcp_access_token=mcp_access_token,
        mcp_refresh_token=mcp_refresh_token,
        mcp_expires_in=token_response.get("expires_in"),
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        bot_id=bot_id,
    )

    redirect_url = _build_return_url(
        base_url=settings.return_base_url,
        target=return_path,
        params={
            "status": "success",
            "spaceId": view.space_id,
            "processId": view.process_id,
            "workspaceId": view.workspace_id or "",
            "mcp": "connected",
        },
    )
    return RedirectResponse(url=redirect_url, status_code=303)


async def clear_notion_mcp_credentials(
    *,
    event_store: EventStore,
    credentials: NotionCredentials,
    space_id: str,
    user_id: str,
    clock: Clock,
    logger: Any,
) -> None:
    expires_in: int | None = None
    if credentials.token_expires_at:
        expires_in = _seconds_left(credentials.token_expires_at, clock)
    await _upsert_notion_integration(
        space_id=space_id,
        user_id=user_id,
        event_store=event_store,
        clock=clock,
        logger=logger,
        mcp_access_token=None,
        mcp_refresh_token=None,
        mcp_expires_in=None,
        access_token=credentials.access_token,
        refresh_token=credentials.refresh_token,
        token_expires_in=expires_in,
        workspace_id=credentials.workspace_id,
        workspace_name=credentials.workspace_name,
        bot_id=credentials.bot_id,
    )
    logger.info("Cleared Notion MCP credentials for space %s", space_id)


async def ensure_fresh_notion_credentials(
    *,
    event_store: EventStore,
    credentials: NotionCredentials,
    space_id: str,
    user_id: str,
    clock: Clock,
    logger: Any,
) -> NotionCredentials:
    # Without classic OAuth we simply return the stored credentials.
    return credentials


async def get_mcp_access_token(
    *,
    credentials: NotionCredentials,
    logger: Any,
) -> str:
    if not credentials.mcp_refresh_token:
        logger.warning(
            "Space %s is missing Notion MCP OAuth credentials.",
            credentials.process_id,
        )
        raise HTTPException(
            status_code=401,
            detail="Notion MCP is not connected for this space.",
        )

    if (
        credentials.mcp_access_token
        and credentials.mcp_token_expires_at
        and credentials.mcp_token_expires_at > datetime.now(UTC)
    ):
        return credentials.mcp_access_token

    settings = _get_mcp_settings()
    payload: dict[str, Any] = {
        "grant_type": "refresh_token",
        "refresh_token": credentials.mcp_refresh_token,
        "resource": NOTION_MCP_RESOURCE,
    }
    if settings.scope:
        payload["scope"] = settings.scope

    logger.debug(
        "Requesting fresh Notion MCP access token via %s",
        settings.token_endpoint,
    )

    token_response = await _request_oauth_token(
        payload=payload,
        logger=logger,
        endpoint=settings.token_endpoint,
        client_id=settings.client_id,
        client_secret=settings.client_secret,
        auth_method=settings.token_auth_method,
        form_encode=True,
    )

    access_token = token_response.get("access_token")
    if not isinstance(access_token, str) or not access_token.strip():
        logger.error(
            "Notion MCP token exchange response missing access_token: %s",
            token_response,
        )
        raise HTTPException(
            status_code=502,
            detail="Notion MCP token exchange returned an invalid response.",
        )
    return access_token


def _initiate_oauth_flow(
    *,
    authorize_endpoint: str,
    base_params: dict[str, Any],
    redis_client: Redis,
    state_ttl_seconds: int,
    state_cache_prefix: str,
    state_payload: dict[str, Any],
) -> tuple[str, str]:
    state = secrets.token_urlsafe(32)
    redis_client.setex(
        f"{state_cache_prefix}{state}", state_ttl_seconds, json.dumps(state_payload)
    )
    params = dict(base_params)
    params["state"] = state
    authorize_url = f"{authorize_endpoint}?{urlencode(params)}"
    return state, authorize_url


def _read_oauth_state(
    *,
    redis_client: Redis,
    state_cache_prefix: str,
    state: str | None,
    missing_detail: str,
) -> dict[str, Any]:
    if not state:
        raise HTTPException(status_code=400, detail=missing_detail)

    cache_key = f"{state_cache_prefix}{state}"
    cached_state_raw = redis_client.get(cache_key)
    if cached_state_raw is None:
        raise HTTPException(status_code=400, detail="Unknown or expired OAuth state.")
    redis_client.delete(cache_key)

    try:
        decoded = (
            cached_state_raw.decode("utf-8")
            if isinstance(cached_state_raw, (bytes, bytearray))
            else str(cached_state_raw)
        )
        return json.loads(decoded)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=400, detail="Corrupted OAuth state payload."
        ) from exc


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


def _build_return_url(
    *,
    base_url: str | None,
    target: str,
    params: dict[str, str],
) -> str:
    destination = target
    parsed = urlparse(destination)
    if not parsed.scheme and base_url:
        destination = urljoin(base_url.rstrip("/") + "/", destination.lstrip("/"))

    filtered_params = {k: v for k, v in params.items() if v is not None}
    if filtered_params:
        separator = "&" if "?" in destination else "?"
        destination = f"{destination}{separator}{urlencode(filtered_params)}"
    return destination


async def _request_oauth_token(
    *,
    payload: dict[str, Any],
    logger: Any,
    endpoint: str,
    client_id: str,
    client_secret: str,
    auth_method: str,
    form_encode: bool = False,
) -> dict[str, Any]:
    headers = {
        "Content-Type": (
            "application/x-www-form-urlencoded" if form_encode else "application/json"
        ),
        "Accept": "application/json",
        "Notion-Version": NOTION_VERSION,
    }

    request_payload = {
        key: value for key, value in payload.items() if value is not None
    }

    if auth_method == "client_secret_basic":
        secret = base64.b64encode(
            f"{client_id}:{client_secret}".encode("utf-8")
        ).decode("utf-8")
        headers["Authorization"] = f"Basic {secret}"
    elif auth_method == "client_secret_post":
        request_payload["client_id"] = client_id
        request_payload["client_secret"] = client_secret
    else:
        raise HTTPException(
            status_code=503,
            detail="Unsupported OAuth client authentication method for Notion token exchange.",
        )

    async with httpx.AsyncClient(timeout=10.0) as client:
        if form_encode:
            form_payload = {k: str(v) for k, v in request_payload.items()}
            response = await client.post(endpoint, data=form_payload, headers=headers)
        else:
            response = await client.post(
                endpoint, json=request_payload, headers=headers
            )

    if response.status_code == 400:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        logger.warning("Notion MCP OAuth returned 400: %s", detail)
        raise HTTPException(status_code=400, detail=detail)

    if not response.is_success:
        logger.error(
            "Unexpected Notion MCP OAuth error %s: %s",
            response.status_code,
            response.text,
        )
        raise HTTPException(
            status_code=502,
            detail="Failed to exchange tokens with Notion MCP OAuth service.",
        )

    return response.json()
