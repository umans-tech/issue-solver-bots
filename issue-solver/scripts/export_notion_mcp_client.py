#!/usr/bin/env python3
"""Print shell exports for the Notion MCP client credentials."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

import httpx

NOTION_MCP_REGISTRATION_ENDPOINT_DEFAULT = "https://mcp.notion.com/register"
NOTION_MCP_TOKEN_AUTH_METHOD_DEFAULT = "client_secret_basic"
NOTION_MCP_CLIENT_NAME_DEFAULT = "Issue Solver MCP"
DEFAULT_MCP_OAUTH_REDIRECT_URI = (
    "http://localhost:8000/integrations/notion/mcp/oauth/callback"
)


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
    except httpx.RequestError as exc:  # pragma: no cover - network error
        raise RuntimeError(f"Unable to register Notion MCP client ({exc}).") from exc

    if response.status_code not in (200, 201):  # pragma: no cover - unexpected
        raise RuntimeError(
            f"Notion MCP registration failed ({response.status_code}): {response.text}"
        )

    try:
        body = response.json()
    except ValueError as exc:  # pragma: no cover - invalid JSON
        raise RuntimeError(
            f"Received invalid payload from Notion MCP registration: {exc}"
        ) from exc

    client_id = body.get("client_id")
    client_secret = body.get("client_secret")
    auth_method = body.get("token_endpoint_auth_method") or default_auth_method

    if not isinstance(client_id, str) or not isinstance(client_secret, str):
        raise RuntimeError("MCP registration did not return client credentials.")

    return client_id, client_secret, auth_method


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Register a new MCP client even if credentials already exist in the environment.",
    )
    args = parser.parse_args()

    existing_id = os.environ.get("NOTION_MCP_CLIENT_ID")
    existing_secret = os.environ.get("NOTION_MCP_CLIENT_SECRET")
    existing_auth_method = os.environ.get(
        "NOTION_MCP_TOKEN_AUTH_METHOD", NOTION_MCP_TOKEN_AUTH_METHOD_DEFAULT
    )

    if existing_id and existing_secret and not args.force:
        print(f"export NOTION_MCP_CLIENT_ID={existing_id}")
        print(f"export NOTION_MCP_CLIENT_SECRET={existing_secret}")
        print(f"export NOTION_MCP_TOKEN_AUTH_METHOD={existing_auth_method}")
        return

    registration_endpoint = os.environ.get(
        "NOTION_MCP_REGISTRATION_ENDPOINT", NOTION_MCP_REGISTRATION_ENDPOINT_DEFAULT
    )
    redirect_uri = os.environ.get(
        "NOTION_MCP_OAUTH_REDIRECT_URI", DEFAULT_MCP_OAUTH_REDIRECT_URI
    )

    client_name = os.environ.get(
        "NOTION_MCP_CLIENT_NAME", NOTION_MCP_CLIENT_NAME_DEFAULT
    )
    auth_method = os.environ.get(
        "NOTION_MCP_TOKEN_AUTH_METHOD", NOTION_MCP_TOKEN_AUTH_METHOD_DEFAULT
    )

    try:
        client_id, client_secret, auth_method = _register_mcp_client(
            registration_endpoint=registration_endpoint,
            redirect_uri=redirect_uri,
            client_name=client_name,
            default_auth_method=auth_method,
        )
    except RuntimeError as exc:
        print(f"[export-notion-mcp-client] {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"export NOTION_MCP_CLIENT_ID={client_id}")
    print(f"export NOTION_MCP_CLIENT_SECRET={client_secret}")
    print(f"export NOTION_MCP_TOKEN_AUTH_METHOD={auth_method}")


if __name__ == "__main__":
    main()
