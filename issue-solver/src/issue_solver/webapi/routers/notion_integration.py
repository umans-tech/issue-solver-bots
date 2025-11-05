from __future__ import annotations

import base64
import json
import os
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Annotated, Any
from urllib.parse import urlencode, urljoin, urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from redis import Redis

from issue_solver.clock import Clock
from issue_solver.events.domain import (
    NotionIntegrationAuthorized,
    NotionIntegrationAuthorizationFailed,
    NotionIntegrationTokenRefreshed,
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
MCP_RECONNECT_MESSAGE = "Notion MCP credentials have expired. Reconnect the Notion MCP integration to continue."

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
        return_base_url=os.environ.get("NOTION_MCP_RETURN_BASE_URL"),
    )


def _seconds_left(timestamp: datetime | None, clock: Clock) -> int | None:
    if not timestamp:
        return None
    remaining = int((timestamp - clock.now()).total_seconds())
    return max(0, remaining)


def _build_integration_view(
    *,
    space_id: str,
    base_event: NotionIntegrationAuthorized,
    credentials: NotionCredentials | None,
) -> NotionIntegrationView:
    workspace_id = (
        credentials.workspace_id
        if credentials and credentials.workspace_id
        else base_event.workspace_id
    )
    workspace_name = (
        credentials.workspace_name
        if credentials and credentials.workspace_name
        else base_event.workspace_name
    )
    bot_id = (
        credentials.bot_id if credentials and credentials.bot_id else base_event.bot_id
    )
    token_expires_at = None
    has_mcp_token = bool(credentials and credentials.mcp_refresh_token)
    process_id = credentials.process_id if credentials else base_event.process_id

    return NotionIntegrationView(
        space_id=space_id,
        process_id=process_id,
        connected_at=base_event.occurred_at,
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        bot_id=bot_id,
        token_expires_at=token_expires_at,
        has_mcp_token=has_mcp_token,
    )


@router.get("/{space_id}", status_code=200)
async def get_notion_integration(
    space_id: str,
    event_store: Annotated[EventStore, Depends(get_event_store)],
) -> NotionIntegrationView:
    base_event = await get_notion_integration_event(event_store, space_id)
    if not base_event:
        raise HTTPException(
            status_code=404,
            detail=f"No Notion integration configured for space {space_id}",
        )

    credentials = await get_notion_credentials(event_store, space_id)
    return _build_integration_view(
        space_id=space_id,
        base_event=base_event,
        credentials=credentials,
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
    settings = _load_mcp_settings()
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
        return _redirect_error(
            settings=settings, return_path=return_path, error_code="missing_space"
        )
    if error:
        return _redirect_error(
            settings=settings, return_path=return_path, error_code=error
        )
    if not code:
        return _redirect_error(
            settings=settings, return_path=return_path, error_code="missing_code"
        )

    try:
        token_response = await _exchange_authorization_code(
            settings=settings,
            code=code,
            logger=logger,
        )
        base_event = await _persist_mcp_tokens(
            event_store=event_store,
            clock=clock,
            logger=logger,
            space_id=space_id,
            user_id=user_id,
            token_response=token_response,
        )
    except HTTPException as exc:
        return _redirect_error(
            settings=settings,
            return_path=return_path,
            error_code=_error_code_from_exc(exc.detail),
        )

    credentials = await get_notion_credentials(event_store, space_id)
    view = _build_integration_view(
        space_id=space_id,
        base_event=base_event,
        credentials=credentials,
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


async def ensure_fresh_notion_credentials(
    *,
    event_store: EventStore,
    credentials: NotionCredentials,
    space_id: str,
    user_id: str,
    clock: Clock,
    logger: Any,
) -> NotionCredentials:
    if not _has_refresh_token(credentials):
        return credentials

    if not _requires_refresh(credentials, clock):
        return credentials

    settings = _load_mcp_settings()
    logger.info(
        "Refreshing Notion MCP access token for space %s (user=%s)", space_id, user_id
    )

    try:
        token_response = await _refresh_mcp_token(
            settings=settings,
            credentials=credentials,
            logger=logger,
        )
    except HTTPException as exc:
        if _is_invalid_grant(exc):
            await _record_refresh_failure(
                event_store=event_store,
                clock=clock,
                user_id=user_id,
                space_id=space_id,
                credentials=credentials,
                detail=str(exc.detail),
            )
            raise HTTPException(status_code=401, detail=MCP_RECONNECT_MESSAGE) from exc
        raise

    return await _persist_refreshed_credentials(
        event_store=event_store,
        clock=clock,
        user_id=user_id,
        space_id=space_id,
        credentials=credentials,
        token_response=token_response,
        logger=logger,
    )


def _has_refresh_token(credentials: NotionCredentials) -> bool:
    return bool(credentials.mcp_refresh_token)


def _requires_refresh(credentials: NotionCredentials, clock: Clock) -> bool:
    if not credentials.mcp_access_token:
        return True
    remaining = _seconds_left(credentials.mcp_token_expires_at, clock)
    return remaining is None or remaining <= 60


async def _refresh_mcp_token(
    *, settings: NotionMcpSettings, credentials: NotionCredentials, logger: Any
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "grant_type": "refresh_token",
        "refresh_token": credentials.mcp_refresh_token,
        "resource": NOTION_MCP_RESOURCE,
    }
    if settings.redirect_uri:
        payload["redirect_uri"] = settings.redirect_uri
    if settings.scope:
        payload["scope"] = settings.scope

    return await _request_oauth_token(
        payload=payload,
        logger=logger,
        endpoint=settings.token_endpoint,
        client_id=settings.client_id,
        client_secret=settings.client_secret,
        auth_method=settings.token_auth_method,
        form_encode=True,
    )


def _is_invalid_grant(exc: HTTPException) -> bool:
    detail = str(exc.detail)
    return exc.status_code in {400, 401} and "invalid_grant" in detail.lower()


async def _record_refresh_failure(
    *,
    event_store: EventStore,
    clock: Clock,
    user_id: str,
    space_id: str,
    credentials: NotionCredentials,
    detail: str,
) -> None:
    failure = NotionIntegrationAuthorizationFailed(
        occurred_at=clock.now(),
        error_type="invalid_grant",
        error_message=detail,
        user_id=user_id,
        space_id=space_id,
        process_id=credentials.process_id,
    )
    await event_store.append(credentials.process_id, failure)


async def _persist_refreshed_credentials(
    *,
    event_store: EventStore,
    clock: Clock,
    user_id: str,
    space_id: str,
    credentials: NotionCredentials,
    token_response: dict[str, Any],
    logger: Any,
) -> NotionCredentials:
    access_token = token_response.get("access_token")
    if not isinstance(access_token, str) or not access_token.strip():
        logger.error(
            "Notion MCP refresh response missing access_token: %s", token_response
        )
        raise HTTPException(
            status_code=502,
            detail="Notion MCP token refresh returned an invalid response.",
        )

    new_refresh_token = (
        token_response.get("refresh_token") or credentials.mcp_refresh_token
    )
    workspace_id = token_response.get("workspace_id") or credentials.workspace_id
    workspace_name = token_response.get("workspace_name") or credentials.workspace_name
    bot_id = token_response.get("bot_id") or credentials.bot_id
    expires_at = _expires_at(clock, token_response.get("expires_in"))

    rotation = NotionIntegrationTokenRefreshed(
        occurred_at=clock.now(),
        user_id=user_id,
        space_id=space_id,
        process_id=credentials.process_id,
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        bot_id=bot_id,
        mcp_access_token=access_token,
        mcp_refresh_token=new_refresh_token,
        mcp_token_expires_at=expires_at,
    )
    await event_store.append(credentials.process_id, rotation)

    logger.info("Refreshed Notion MCP access token for space %s", space_id)

    return NotionCredentials(
        mcp_access_token=access_token,
        mcp_refresh_token=new_refresh_token,
        mcp_token_expires_at=expires_at,
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        bot_id=bot_id,
        process_id=credentials.process_id,
    )


def _load_mcp_settings() -> NotionMcpSettings:
    try:
        return _get_mcp_settings()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _redirect_error(
    *, settings: NotionMcpSettings, return_path: str, error_code: str
) -> RedirectResponse:
    redirect_url = _build_return_url(
        base_url=settings.return_base_url,
        target=return_path,
        params={"status": "error", "error": error_code},
    )
    return RedirectResponse(url=redirect_url, status_code=303)


def _error_code_from_exc(detail: Any) -> str:
    if isinstance(detail, dict):
        return detail.get("error") or detail.get("error_description") or "unknown_error"
    return str(detail)


async def _exchange_authorization_code(
    *, settings: NotionMcpSettings, code: str, logger: Any
) -> dict[str, Any]:
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.redirect_uri,
        "resource": NOTION_MCP_RESOURCE,
    }
    if settings.scope:
        payload["scope"] = settings.scope

    return await _request_oauth_token(
        payload=payload,
        logger=logger,
        endpoint=settings.token_endpoint,
        client_id=settings.client_id,
        client_secret=settings.client_secret,
        auth_method=settings.token_auth_method,
        form_encode=True,
    )


async def _persist_mcp_tokens(
    *,
    event_store: EventStore,
    clock: Clock,
    logger: Any,
    space_id: str,
    user_id: str,
    token_response: dict[str, Any],
) -> NotionIntegrationAuthorized:
    access_token = token_response.get("access_token")
    refresh_token = token_response.get("refresh_token")
    if not access_token or not refresh_token:
        raise HTTPException(status_code=400, detail="invalid_mcp_token_response")

    workspace_id = token_response.get("workspace_id")
    workspace_name = token_response.get("workspace_name")
    bot_id = token_response.get("bot_id")
    expires_at = _expires_at(clock, token_response.get("expires_in"))

    existing = await get_notion_integration_event(event_store, space_id)
    if existing:
        rotation = NotionIntegrationTokenRefreshed(
            occurred_at=clock.now(),
            user_id=user_id,
            space_id=space_id,
            process_id=existing.process_id,
            workspace_id=workspace_id or existing.workspace_id,
            workspace_name=workspace_name or existing.workspace_name,
            bot_id=bot_id or existing.bot_id,
            mcp_access_token=access_token,
            mcp_refresh_token=refresh_token,
            mcp_token_expires_at=expires_at,
        )
        await event_store.append(existing.process_id, rotation)
        logger.info("Notion MCP tokens rotated for space %s", space_id)
        return existing

    process_id = str(uuid.uuid4())
    connected = NotionIntegrationAuthorized(
        occurred_at=clock.now(),
        user_id=user_id,
        space_id=space_id,
        process_id=process_id,
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        bot_id=bot_id,
        mcp_access_token=access_token,
        mcp_refresh_token=refresh_token,
        mcp_token_expires_at=expires_at,
    )
    await event_store.append(process_id, connected)
    logger.info(
        "Notion MCP integration created for space %s (process=%s)", space_id, process_id
    )
    return connected


def _expires_at(clock: Clock, expires_in: Any) -> datetime | None:
    if isinstance(expires_in, (int, float)) and expires_in > 0:
        return clock.now() + timedelta(seconds=int(expires_in))
    return None


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
