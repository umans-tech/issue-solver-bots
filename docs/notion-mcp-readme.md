# Notion MCP Integration – Current Flow

> The classic Notion OAuth flow has been retired. The integration now relies **only** on Notion's Model Context Protocol (MCP) authorization.

## End-to-End Flow

1. **User starts the flow**
   - Frontend calls `POST /api/notion/oauth/start` (Next.js route).  
   - This proxies to FastAPI `GET /integrations/notion/oauth/mcp/start`, which builds the Notion authorization URL, stores a short-lived state in Redis, and returns it to the browser.

2. **User approves in Notion**
   - Notion presents the MCP consent dialog.
   - On success Notion redirects back to `GET /integrations/notion/mcp/oauth/callback`.

3. **Backend stores MCP credentials**
   - FastAPI exchanges the authorization code for an MCP refresh token.
   - The refresh token is encrypted and appended to the event stream (`NotionIntegrationConnected` / `NotionIntegrationTokenRotated`).
   - No classic access token is stored; the integration is considered "connected" when an MCP refresh token exists.

4. **Proxying tool calls**
   - The UI sends JSON-RPC payloads to `POST /mcp/notion/proxy`.  
   - The proxy loads the stored credentials, refreshes them if necessary, exchanges for an MCP access token, and forwards the request to `https://mcp.notion.com/mcp`.
   - Responses are streamed back verbatim so the MCP client can decode them.

## Required Environment Variables

Add the following variables to FastAPI:

```bash
NOTION_MCP_CLIENT_ID=...
NOTION_MCP_CLIENT_SECRET=...
# Optional overrides
# NOTION_MCP_OAUTH_REDIRECT_URI="https://api.example.com/integrations/notion/mcp/oauth/callback"
# NOTION_MCP_RETURN_BASE_URL="https://app.example.com"
# NOTION_MCP_TOKEN_AUTH_METHOD="client_secret_post"
# NOTION_MCP_TOKEN_SCOPE="..."
# NOTION_MCP_STATE_TTL_SECONDS=600
```

Frontend (Next.js) still requires `CUDU_ENDPOINT` so the MCP client knows where to proxy requests.

## Local Development Notes

- Run FastAPI and Next.js locally, then set `NOTION_MCP_OAUTH_REDIRECT_URI=http://localhost:8000/integrations/notion/mcp/oauth/callback` and `NOTION_MCP_RETURN_BASE_URL=http://localhost:3000` to get end-to-end redirects working.
- Generate client credentials once using `just export-notion-mcp-credentials` and reuse them.
- When testing, you can clear credentials with `ensure_fresh_notion_credentials` or by removing the integration from the Notion UI.

## UI Expectations

- The integration dialog only references MCP. Once a refresh token is stored the status moves to **MCP connected**.
- If the proxy returns `invalid_grant`, the backend clears the stored refresh token and the UI prompts the user to reconnect.

## Troubleshooting

| Symptom | Typical Cause | Fix |
| --- | --- | --- |
| `401 Missing Notion MCP tokens` | User never completed the MCP consent dialog | Re-run the connect flow |
| `invalid_grant` in logs | Stored refresh token revoked in Notion | User must reconnect |
| Chat tools missing | Frontend MCP client failed to initialise | Check `CUDU_ENDPOINT` and browser console |
| Proxy returns `500` | Stale MCP access token and refresh failed | Clear credentials (`clear_notion_mcp_credentials`) and reconnect |

The integration is now fully MCP-centric: there are no classic OAuth tokens or endpoints to maintain.
