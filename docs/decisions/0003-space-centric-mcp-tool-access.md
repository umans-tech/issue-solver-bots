# 3. Space-centric MCP Tool Access

Date: 2025-01-17

## Status

Accepted

## Context

The MCP (Model Context Protocol) tools proxy was implementing user-centric repository access, where only the user who originally connected a repository to a space could access MCP tools. This conflicted with the space-centric collaboration model where all users within a space should have access to shared resources.

**Problem**: Repository connections were filtered by both `user_id` and `space_id`, causing MCP tools to be unavailable to other space members who didn't originally connect the repository.

**Impact**: 
- Inconsistent tool availability within teams
- Broken shared workspace functionality
- Poor user adoption of MCP features

## Decision

We will implement **space-centric repository access** for MCP tools:

1. **Repository Lookup**: The `get_connected_repo_event` function will filter by `space_id` only, allowing any space member to access repositories connected to that space
2. **Security**: Space membership validation remains handled at the API gateway/authentication layer
3. **Backward Compatibility**: The `user_id` parameter is retained but unused to maintain API compatibility

## Consequences

**Positive**:
- All space members can access MCP tools for repositories connected to their space
- Consistent with space-centric collaboration model
- Improved user experience and tool adoption
- Simpler access logic aligned with domain model

**Negative**:
- Slightly relaxed access control (mitigated by space membership validation at auth layer)
- Potential for confusion during transition period

**Risks Mitigated**:
- Space membership is still validated by the auth layer before requests reach the MCP proxy
- Repository tokens remain secured and associated with the original connection process
- Cross-space access is prevented by space_id filtering

## Implementation

Modified `/issue-solver/src/issue_solver/webapi/routers/mcp_repositories_proxy.py`:
- `get_connected_repo_event()` now queries by `{"space_id": space_id}` only
- Added explicit space_id validation with clear error messages
- Enhanced documentation explaining the space-centric access model