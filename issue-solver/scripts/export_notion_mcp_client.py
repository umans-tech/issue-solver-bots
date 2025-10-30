#!/usr/bin/env python3
"""Print shell exports for the Notion MCP client credentials."""

from __future__ import annotations

import argparse
import logging
import os
from typing import Any

import httpx

module_logger = logging.getLogger(__name__)


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
    existing_token_auth_method = os.environ.get(
        "NOTION_MCP_TOKEN_AUTH_METHOD", "client_secret_basic"
    )

    if existing_id and existing_secret and not args.force:
        print(f"export NOTION_MCP_CLIENT_ID={existing_id}")
        print(f"export NOTION_MCP_CLIENT_SECRET={existing_secret}")
        print(f"export NOTION_MCP_TOKEN_AUTH_METHOD={existing_token_auth_method}")
        return

    client_id, client_secret, auth_method = register_mcp_client()
    print(f"export NOTION_MCP_CLIENT_ID={client_id}")
    print(f"export NOTION_MCP_CLIENT_SECRET={client_secret}")
    print(f"export NOTION_MCP_TOKEN_AUTH_METHOD={auth_method}")


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


def register_mcp_client(*, persist: bool = False) -> tuple[str, str, str]:
    registration_endpoint = "https://mcp.notion.com/register"
    if not registration_endpoint:
        raise RuntimeError(
            "Notion MCP registration endpoint is not available. "
            "Set NOTION_MCP_REGISTRATION_ENDPOINT or ensure the MCP metadata "
            "exposes it before attempting registration."
        )
    mcp_client_name = os.environ.get("NOTION_MCP_CLIENT_NAME", "Umans AI MCP")
    mcp_redirect_uri = os.environ.get("NOTION_MCP_OAUTH_REDIRECT_URI")
    if not mcp_redirect_uri:
        raise RuntimeError(
            "Notion MCP OAuth redirect uri is not available. "
            "Set NOTION_MCP_OAUTH_REDIRECT_URI or ensure the MCP "
        )
    client_id, client_secret, auth_method = _register_mcp_client(
        registration_endpoint=registration_endpoint,
        redirect_uri=mcp_redirect_uri,
        client_name=mcp_client_name,
        default_auth_method=os.environ.get(
            "NOTION_MCP_TOKEN_AUTH_METHOD", "client_secret_basic"
        ),
    )
    if persist:
        os.environ["NOTION_MCP_CLIENT_ID"] = client_id
        os.environ["NOTION_MCP_CLIENT_SECRET"] = client_secret
        os.environ["NOTION_MCP_TOKEN_AUTH_METHOD"] = auth_method
    result = client_id, client_secret, auth_method
    return result


if __name__ == "__main__":
    main()
