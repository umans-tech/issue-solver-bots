"""GitHub MCP Proxy Router for Issue Solver."""

import logging
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from httpx import Response

from issue_solver.events.event_store import EventStore
from issue_solver.events.domain import CodeRepositoryConnected, most_recent_event
from issue_solver.webapi.dependencies import get_event_store, get_logger

router = APIRouter()


@router.post("/mcp/repositories/proxy")
async def proxy_code_repo_mcp(
    request: dict[str, Any],
    event_store: Annotated[EventStore, Depends(get_event_store)],
    logger: Annotated[
        logging.Logger | logging.LoggerAdapter,
        Depends(lambda: get_logger("issue_solver.webapi.routers.github_mcp")),
    ],
) -> dict[str, Any]:
    """Proxy for Code Repository MCP requests to Remote MCP server.
    (So far, only GitHub MCP is supported)"""

    logger.info("Processing GitHub MCP proxy request")

    try:
        user_id = request.get("meta", {}).get("user_id")
        space_id = request.get("meta", {}).get("space_id")

        code_repo_was_connected = await get_connected_repo_event(
            event_store, space_id, user_id
        )

        if not code_repo_was_connected:
            raise HTTPException(
                status_code=401,
                detail="No repository connected. Please connect a Code repository.",
            )

        access_token = code_repo_was_connected.access_token

        if not access_token or access_token.strip() == "":
            raise HTTPException(
                status_code=401,
                detail="No valid access token found for repository. Please reconnect the repository with proper authentication.",
            )

        logger.info(
            f"Using access token for repository: {code_repo_was_connected.url} (user: {user_id}, space: {space_id})"
        )

        if "github.com" in code_repo_was_connected.url.lower():
            result = await proxy_github_mcp(access_token, request)
            logger.info("Successfully proxied GitHub MCP request")
            return result
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
        logger.error(f"Unexpected error in GitHub MCP proxy: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while processing GitHub MCP request.",
        )


async def proxy_github_mcp(access_token, request):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "Issue-Solver-MCP-Proxy/1.0",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.githubcopilot.com/mcp/", json=request, headers=headers
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

        return await format_response(response)


async def get_connected_repo_event(
    event_store, space_id, user_id
) -> CodeRepositoryConnected | None:
    connected_repo_event = None
    if user_id and space_id:
        events = await event_store.find(
            {"user_id": user_id, "space_id": space_id}, CodeRepositoryConnected
        )
        connected_repo_event = most_recent_event(events, CodeRepositoryConnected)
    return connected_repo_event


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
