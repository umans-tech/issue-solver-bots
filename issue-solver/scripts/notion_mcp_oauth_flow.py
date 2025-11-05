#!/usr/bin/env python3
"""
Minimal helper to complete the Notion MCP OAuth flow locally.

Workflow:
1. Starts a tiny HTTP server bound to NOTION_MCP_OAUTH_REDIRECT_URI.
2. Prints the authorization URL you need to open in a browser.
3. After you approve the consent screen, captures the authorization code + state,
   prints them to stdout, exchanges the code for tokens, and saves the result in
   `.notion_mcp_tokens.json`.

Environment variables expected (all required):
  - NOTION_MCP_CLIENT_ID
  - NOTION_MCP_CLIENT_SECRET
  - NOTION_MCP_OAUTH_REDIRECT_URI (must point to http://localhost:<port>/...)

Optional overrides:
  - NOTION_MCP_AUTHORIZATION_ENDPOINT (default https://mcp.notion.com/authorize)
  - NOTION_MCP_TOKEN_ENDPOINT (default https://mcp.notion.com/token)
  - NOTION_MCP_RESOURCE (default https://mcp.notion.com)
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import queue
import secrets
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, Tuple
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

AUTHORIZATION_ENDPOINT = os.environ.get(
    "NOTION_MCP_AUTHORIZATION_ENDPOINT", "https://mcp.notion.com/authorize"
)
TOKEN_ENDPOINT = os.environ.get(
    "NOTION_MCP_TOKEN_ENDPOINT", "https://mcp.notion.com/token"
)
RESOURCE = os.environ.get("NOTION_MCP_RESOURCE", "https://mcp.notion.com")
STATE_PATH = Path(__file__).resolve().parent.parent / ".notion_mcp_pkce.json"
TOKENS_PATH = Path(__file__).resolve().parent.parent / ".notion_mcp_tokens.json"


def _require_env(name: str) -> str:
    try:
        value = os.environ[name]
    except KeyError as exc:  # pragma: no cover - env guarantees simplicity
        raise SystemExit(f"[notion-mcp-oauth] Missing required env var: {name}") from exc
    if not value:
        raise SystemExit(f"[notion-mcp-oauth] Environment variable {name} is empty.")
    return value


def _generate_pkce() -> Tuple[str, str]:
    verifier = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip("=")
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).decode().rstrip("=")
    return verifier, challenge


def _build_authorization_url(
    client_id: str,
    redirect_uri: str,
    code_challenge: str,
    state: str,
) -> str:
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
        "resource": RESOURCE,
    }
    return f"{AUTHORIZATION_ENDPOINT}?{urlencode(params)}"


def _start_callback_server(
    host: str,
    port: int,
    path: str,
) -> Tuple[HTTPServer, queue.Queue[Dict[str, Any]]]:
    received: queue.Queue[Dict[str, Any]] = queue.Queue()

    class _CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # pragma: no cover - interactive flow
            parsed = urlparse(self.path)
            if parsed.path != path:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Unexpected path.")
                return

            params = parse_qs(parsed.query)
            code = params.get("code", [None])[0]
            state_val = params.get("state", [None])[0]
            if not code or not state_val:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing code or state in query string.")
                return

            received.put({"code": code, "state": state_val})

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Notion MCP OAuth captured.</h1>"
                b"<p>You can return to the terminal; this window can be closed.</p>"
                b"</body></html>"
            )

        def log_message(self, format: str, *args: Any) -> None:  # pragma: no cover
            # Silence default stdout logging to keep script output minimal.
            return

    try:
        server = HTTPServer((host, port), _CallbackHandler)
    except OSError as exc:  # pragma: no cover - port in use is a user issue
        raise SystemExit(
            f"[notion-mcp-oauth] Unable to bind to {host}:{port} "
            f"(maybe the web API is running?): {exc}"
        ) from exc

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, received


def _exchange_code(
    *,
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
    code_verifier: str,
) -> Dict[str, Any]:
    form = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
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
    return response.json()


def main() -> int:
    client_id = _require_env("NOTION_MCP_CLIENT_ID")
    client_secret = _require_env("NOTION_MCP_CLIENT_SECRET")
    redirect_uri = _require_env("NOTION_MCP_OAUTH_REDIRECT_URI")

    parsed_redirect = urlparse(redirect_uri)
    if parsed_redirect.scheme != "http":
        raise SystemExit(
            "[notion-mcp-oauth] Redirect URI must use http:// for local testing."
        )
    host = parsed_redirect.hostname or "localhost"
    port = parsed_redirect.port or 80
    path = parsed_redirect.path or "/"

    code_verifier, code_challenge = _generate_pkce()
    state = secrets.token_urlsafe(16)

    STATE_PATH.write_text(
        json.dumps(
            {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "code_verifier": code_verifier,
                "state": state,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    server, received_queue = _start_callback_server(host, port, path)

    authorize_url = _build_authorization_url(
        client_id=client_id,
        redirect_uri=redirect_uri,
        code_challenge=code_challenge,
        state=state,
    )

    print("Open this URL in your browser and approve the integration:\n")
    print(authorize_url)
    print()
    print("Waiting for the redirect with the authorization code...")

    try:
        payload = received_queue.get(timeout=600)
    except queue.Empty:  # pragma: no cover - interactive timeout
        server.shutdown()
        raise SystemExit("[notion-mcp-oauth] Timed out waiting for the callback.")

    server.shutdown()
    server.server_close()

    received_code = payload["code"]
    received_state = payload["state"]

    print(f"\nAuthorization code: {received_code}")
    print(f"State returned:     {received_state}")

    if received_state != state:
        raise SystemExit("[notion-mcp-oauth] State mismatch; aborting.")

    try:
        tokens = _exchange_code(
            client_id=client_id,
            client_secret=client_secret,
            code=received_code,
            redirect_uri=redirect_uri,
            code_verifier=code_verifier,
        )
    except httpx.HTTPStatusError as exc:  # pragma: no cover - depends on Notion response
        raise SystemExit(
            f"[notion-mcp-oauth] Token request failed: {exc.response.status_code} {exc.response.text}"
        ) from exc

    TOKENS_PATH.write_text(json.dumps(tokens, indent=2), encoding="utf-8")

    print("\nAccess token response received and stored in .notion_mcp_tokens.json:")
    print(json.dumps(tokens, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
