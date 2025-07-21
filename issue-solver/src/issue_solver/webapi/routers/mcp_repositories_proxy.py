"""GitHub MCP Proxy Router for Issue Solver."""

import logging
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from httpx import Response
from starlette.responses import StreamingResponse
from starlette.responses import Response as StarletteResponse

from issue_solver.events.event_store import EventStore
from issue_solver.events.code_repo_integration import (
    get_access_token,
    get_connected_repo_event,
)
from issue_solver.webapi.dependencies import get_event_store, get_logger

router = APIRouter()


@router.get("/mcp/repositories/proxy")
async def proxy_code_repo_mcp_stream(request: Request) -> StarletteResponse:  # type: ignore[name-defined]
    session_id = request.headers.get("mcp-session-id")
    if session_id is None:
        # According to the spec the header is mandatory for the stream
        return JSONResponse(
            status_code=400, content={"detail": "Missing mcp-session-id header"}
        )

    headers = {
        "mcp-session-id": session_id,
        "User-Agent": "Issue-Solver-MCP-Proxy/1.0",
        "Accept": "text/event-stream",
    }

    async def event_stream():
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "GET", "https://api.githubcopilot.com/mcp/", headers=headers
            ) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes():
                    yield chunk

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/mcp/repositories/proxy")
async def proxy_code_repo_mcp(
    raw_request: Request,
    event_store: Annotated[EventStore, Depends(get_event_store)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(lambda: get_logger("issue_solver.webapi.routers.github_mcp")),
    ],
) -> JSONResponse:
    """Proxy for Code Repository MCP requests to Remote MCP server.
    (So far, only GitHub MCP is supported)"""

    logger.info("Processing GitHub MCP proxy request")

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

        code_repo_was_connected = await get_connected_repo_event(event_store, space_id)

        if not code_repo_was_connected:
            raise HTTPException(
                status_code=404,
                detail="No repository connected to this space. Please connect a Code repository to enable MCP tools.",
            )

        access_token = await get_access_token(
            event_store, code_repo_was_connected.process_id
        )

        if not access_token or access_token.strip() == "":
            raise HTTPException(
                status_code=401,
                detail="No valid access token found for repository. Please reconnect the repository with proper authentication.",
            )

        logger.info(
            f"Using access token for repository: {code_repo_was_connected.url} (user: {user_id}, space: {space_id})"
        )

        if "github.com" in code_repo_was_connected.url.lower():
            result, outgoing_session_id = await proxy_github_mcp(
                access_token, payload, incoming_session_id
            )
            logger.info("Successfully proxied GitHub MCP request")

            response_json = JSONResponse(content=result)
            if outgoing_session_id:
                response_json.headers["mcp-session-id"] = outgoing_session_id
            return response_json
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported repository URL. Only GitHub repositories are supported so far.",
            )

    except httpx.RequestError as e:
        logger.error(f"Network error connecting to GitHub MCP server: {e}")
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to GitHub MCP server. Please try again later.",
        )
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"Unexpected error in GitHub MCP proxy: {e}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error while processing GitHub MCP request.",
            )
        raise e


async def proxy_github_mcp(
    access_token: str, payload: dict[str, Any], incoming_session_id: str | None = None
) -> tuple[dict[str, Any], str | None]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "Issue-Solver-MCP-Proxy/1.0",
    }

    if incoming_session_id:
        headers["mcp-session-id"] = incoming_session_id
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.githubcopilot.com/mcp/", json=payload, headers=headers
        )

        if response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="GitHub authentication failed. Please check your repository connection.",
            )

        if not response.is_success:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"GitHub MCP server error: {response.text}",
            )

        formatted_response = await format_response(response)
        outgoing_session_id = response.headers.get("mcp-session-id")
        return formatted_response, outgoing_session_id


@router.get("/api/mcp/github/health")
async def github_mcp_health() -> dict[str, str]:
    """Health check endpoint for GitHub MCP proxy."""
    return {"status": "healthy", "service": "github-mcp-proxy"}


async def format_response(response: Response) -> dict[str, Any]:
    try:
        if response.text.strip():
            result = response.json()
        else:
            result = {
                "status": "accepted",
                "message": "Request accepted by GitHub MCP server",
            }
    except ValueError:
        result = {"status": "success", "data": response.text}
    return result
