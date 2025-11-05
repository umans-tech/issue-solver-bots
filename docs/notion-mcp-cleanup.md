# Notion MCP Clean-up Checklist

This document summarises the residual tidy-up work after landing the Notion MCP integration. It focuses on two areas that still contain legacy or duplicated logic from earlier iterations: callback handling and unused configuration paths. No code has been modified; the action items below describe follow-up refactors.

## 1. Align Callback Routes and Redirects

**Current state**

- FastAPI accepts both `/integrations/notion/mcp/oauth/callback` and `/integrations/notion/oauth/mcp/callback` (the latter was an early guess).  
- The UI env examples (`.env.example`, docs) still list both `NOTION_MCP_OAUTH_REDIRECT_URI` variants.  
- Notion’s MCP metadata advertises a single redirect URI; only one needs to exist in production.

**Cleanup steps**

1. Confirm which redirect URI your registered MCP client actually uses (check the developer console entry).  
2. Update `NOTION_MCP_OAUTH_REDIRECT_URI` everywhere (env files, docs, deployment manifests) to that canonical path.  
3. Remove the redundant FastAPI handler, keeping only the supported route.  
4. Verify that the UI’s `useSearchParams` lookups (in `app/integrations/notion/callback/page.tsx`) still work with the remaining handler.

## 2. Drop Stale MCP Configuration Paths

**Current state**

- `_get_oauth_config` still carries optional fields (`NOTION_API_RESOURCE`, `NOTION_MCP_TOKEN_SCOPE`, `mcp_registration_endpoint`) that were introduced while experimenting with dynamic metadata.  
- The env example file lists many commented-out overrides that are no longer required.  
- Documentation in `docs/notion-mcp-integration-investigation.md` references now-removed flows (`NOTION_MCP_TOKEN_ENDPOINT` overrides, alternate resource audiences).

**Cleanup steps**

1. Audit `_get_oauth_config` and remove unused branches (e.g. metadata fetch when defaults are hard-coded, optional scope fields if Notion ignores them).  
2. Trim `.env.example` to the minimal set required for a successful integration: OAuth redirect, MCP redirect, client ID/secret, MCP resource.  
3. Delete obsolete notes in the investigation doc (or replace them with a short “historical notes” section that clearly states they are deprecated).  
4. Ensure tests no longer set environment variables that will be removed; replace with the canonical values.

---

Working through this checklist will leave the MCP code path with a single, well-documented redirect URL and only the configuration knobs that are genuinely needed for the integration to function.
