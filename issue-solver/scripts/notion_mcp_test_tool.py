#!/usr/bin/env python3
"""
Smoke test for the Notion MCP tokens produced by `notion-mcp-oauth-flow`.

The script:
1. Ensures the minimal MCP Python client is available (clones the SDK on first run).
2. Opens a Streamable HTTP connection to https://mcp.notion.com/mcp using the stored access token.
3. Runs `initialize` followed by `tools/list`, printing the results.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Tuple

TOKENS_PATH = Path(__file__).resolve().parent.parent / ".notion_mcp_tokens.json"
SDK_CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache" / "mcp-python-sdk"
MCP_ENDPOINT = "https://mcp.notion.com/mcp"
DEFAULT_NOTION_VERSION = "2025-09-03"


def _ensure_sdk() -> Tuple[Any, Any]:
    """Ensure the MCP Python SDK is importable, cloning it if necessary."""
    try:
        from mcp import ClientSession  # type: ignore
        from mcp.client.streamable_http import streamablehttp_client  # type: ignore
        return ClientSession, streamablehttp_client
    except ImportError:
        pass

    if not SDK_CACHE_DIR.exists():
        SDK_CACHE_DIR.parent.mkdir(parents=True, exist_ok=True)
        print("[notion-mcp-test] Cloning MCP Python SDK (first run)...")
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "https://github.com/modelcontextprotocol/python-sdk", str(SDK_CACHE_DIR)],
            check=False,
        )
        if result.returncode != 0:
            raise SystemExit("[notion-mcp-test] Failed to clone modelcontextprotocol/python-sdk. Check git/network access.")

    sys.path.append(str(SDK_CACHE_DIR / "src"))
    try:
        from mcp import ClientSession  # type: ignore
        from mcp.client.streamable_http import streamablehttp_client  # type: ignore
    except ImportError as exc:  # pragma: no cover - defensive
        raise SystemExit(f"[notion-mcp-test] Unable to import MCP SDK modules: {exc}") from exc

    return ClientSession, streamablehttp_client


def _load_access_token() -> str:
    if not TOKENS_PATH.exists():
        raise SystemExit(
            f"[notion-mcp-test] {TOKENS_PATH} not found. Run `just notion-mcp-oauth-flow` first."
        )
    tokens = json.loads(TOKENS_PATH.read_text(encoding="utf-8"))
    token = tokens.get("access_token")
    if not token:
        raise SystemExit("[notion-mcp-test] Stored tokens missing access_token.")
    return token


async def _run_test() -> None:
    ClientSession, streamablehttp_client = _ensure_sdk()
    token = _load_access_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": os.environ.get("NOTION_MCP_VERSION", DEFAULT_NOTION_VERSION),
    }

    async with streamablehttp_client(MCP_ENDPOINT, headers=headers) as (read_stream, write_stream, _get_session_id):
        async with ClientSession(read_stream, write_stream) as session:
            init_result = await session.initialize()
            server_info = init_result.serverInfo
            print(
                "[notion-mcp-test] initialize -> "
                f"protocol={init_result.protocolVersion}, server={server_info.name} {server_info.version}"
            )

            tools_result = await session.list_tools()
            tool_names = [tool.name for tool in tools_result.tools]
            print(f"[notion-mcp-test] tools/list -> {len(tool_names)} tools")
            for name in tool_names:
                print(f"  - {name}")


def main() -> int:
    try:
        asyncio.run(_run_test())
        return 0
    except Exception as exc:
        print(f"[notion-mcp-test] Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
