# Notion MCP Integration – Working Path & Pitfalls

## High-Level Flow

1. **Standard OAuth**  
   - `/integrations/notion/oauth/start` → user approves via Notion’s classic dialog.  
   - `/integrations/notion/oauth/callback` stores/rotates the Databases API token.  
   - When MCP isn’t connected yet, the callback immediately redirects to the MCP flow.

2. **MCP OAuth**  
   - `/integrations/notion/oauth/mcp/start` (triggered automatically post-OAuth or manually)  
   - User sees the **same** Notion permission screen (Notion doesn’t brand MCP differently yet).  
   - `/integrations/notion/mcp/oauth/callback` exchanges the MCP authorization code for a refresh token and stores it.

3. **MCP Proxy**  
   - Front-end sends JSON-RPC requests to `/mcp/notion/proxy` with space + user metadata.  
   - FastAPI refreshes tokens if needed, exchanges for MCP access token, and forwards the payload to `https://mcp.notion.com/mcp`.  
   - Response is streamed back untouched to the browser so the MCP client can parse JSON-RPC correctly.

4. **Agent Visibility**  
   - UI exposes MCP tools once the client succeeds in discovering them.  
   - Tools are surfaced in the opening assistant message and available in `experimental_activeTools`.  
   - Integration dialog shows “Connected” when both Databases API + MCP refresh tokens exist.

---

## What Worked

- **Token lifecycle** (both Databases API and MCP) handled entirely by the FastAPI backend with refresh logic and event storage.  
- **Proxy headers** fixed (`Accept: application/json, text/event-stream`) so Notion accepts requests.  
- **UI environment**: once `CUDU_ENDPOINT` is set, MCP client creation succeeds.  
- **Dynamic tool discovery**: server logs and agent prompt now list Notion MCP tools when available.  
- **Automatic second redirect**: standard OAuth automatically cascades into MCP consent if needed.

---

## What Didn’t Work (and the Fixes)

| Issue | Root Cause | Resolution |
| --- | --- | --- |
| `404` on MCP callback | Wrong path (`/integrations/notion/oauth/mcp/callback`) vs actual client redirect (`/integrations/notion/mcp/oauth/callback`) | Added handler for the correct path & ensured env uses the same URI |
| MCP tools missing in UI | `CUDU_ENDPOINT` missing / MCP client creation failing silently | Added logging and surfaced the error; set `CUDU_ENDPOINT` in Next.js env |
| `406 Not Acceptable` from Notion MCP | Proxy only sent `Accept: text/event-stream` | Updated header to accept both JSON and event streams |
| JSON-RPC validation errors (Zod) | Proxy wrapped Notion responses in `{status,data}` | Proxy now returns the raw HTTP response body and headers |
| Silent fallback (`noMCPClient`) | Exceptions suppressed | Logged the actual error so reconnection prompts are explicit |
| `invalid_grant` after reconnecting | Old MCP refresh tokens persisted after changing client credentials | Proxy now clears cached MCP tokens and returns a reconnect prompt when Notion reports `invalid_grant`. |

---

## Implementation Checklist

1. **Environment Variables**
   ```bash
   NOTION_OAUTH_REDIRECT_URI=http://localhost:8000/integrations/notion/oauth/callback
   NOTION_MCP_OAUTH_REDIRECT_URI=http://localhost:8000/integrations/notion/mcp/oauth/callback
   NOTION_MCP_CLIENT_ID=…      # from MCP dynamic registration
   NOTION_MCP_CLIENT_SECRET=…
   NOTION_MCP_RESOURCE=https://mcp.notion.com
   CUDU_ENDPOINT=http://localhost:8000   # used by the Next.js MCP client
   ```
   Restart both FastAPI and Next.js after any change. Then run `just export-notion-mcp-credentials` once to generate the MCP client ID/secret and store them in your environment or secrets manager.

2. **Reconnect Flow**
   - Always run through the Notion OAuth dialog and allow the automatic redirect to MCP.  
   - Confirm FastAPI logs show `POST https://mcp.notion.com/mcp "HTTP/1.1 200 OK"`.
3. **UI Verification**
   - On the first assistant reply, ensure the Notion tools are listed.  
   - Server console should log both `[Notion MCP] tools discovered` and `[MCP] available tools`.

4. **Tool Calls**
   - When the agent uses a Notion tool, FastAPI should log `POST /mcp/notion/proxy ... 200`.

---

## Follow-Up Focus Areas

- **UI Messaging**: make it clearer in the dialog that MCP consent follows the standard Notion dialog even though the visual is identical.  
- **Error Surfacing**: consider exposing the backend “Reconnect the integration” signal directly in the UI when MCP tokens expire.  
- **Caching / Refresh**: monitor MCP token rotations to ensure the UI doesn’t hang on stale tool lists (the current logging helps detect this).

With these changes in place, Notion MCP is fully operational: the backend refreshes both token sets, the proxy forwards JSON-RPC untouched, and the Conversational UI lists and uses Notion MCP tools alongside GitHub MCP.
