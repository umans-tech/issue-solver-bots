#!/usr/bin/env python3
"""Refresh the Notion MCP access token using the stored refresh token."""

import json
import os
from pathlib import Path

import httpx

TOKEN_ENDPOINT = os.environ.get(
    "NOTION_MCP_TOKEN_ENDPOINT", "https://mcp.notion.com/token"
)
RESOURCE = os.environ.get("NOTION_MCP_RESOURCE", "https://mcp.notion.com")
TOKENS_PATH = Path(__file__).resolve().parent.parent / ".notion_mcp_tokens.json"


def main() -> int:
    client_id = os.environ.get("NOTION_MCP_CLIENT_ID")
    client_secret = os.environ.get("NOTION_MCP_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise SystemExit(
            "[notion-mcp-refresh] NOTION_MCP_CLIENT_ID and NOTION_MCP_CLIENT_SECRET must be set."
        )

    if not TOKENS_PATH.exists():
        raise SystemExit(
            f"[notion-mcp-refresh] {TOKENS_PATH} does not exist. Run the OAuth flow first."
        )

    tokens = json.loads(TOKENS_PATH.read_text(encoding="utf-8"))
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise SystemExit("[notion-mcp-refresh] No refresh_token found in the stored tokens.")

    form = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "resource": RESOURCE,
    }

    response = httpx.post(
        TOKEN_ENDPOINT,
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        auth=(client_id, client_secret),
        timeout=15.0,
    )
    response.raise_for_status()
    new_tokens = response.json()
    TOKENS_PATH.write_text(json.dumps(new_tokens, indent=2), encoding="utf-8")
    print(json.dumps(new_tokens, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
