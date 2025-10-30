#!/usr/bin/env python3
"""Print shell exports for the Notion MCP client credentials."""

from issue_solver.webapi.routers import notion_integration


def main() -> None:
    config = notion_integration._get_oauth_config()
    print(f"export NOTION_MCP_CLIENT_ID={config.mcp_client_id}")
    print(f"export NOTION_MCP_CLIENT_SECRET={config.mcp_client_secret}")


if __name__ == "__main__":
    main()
