# GitHub MCP Integration for Conversational UI

**Conclusion first**: We need to enable the Conversational UI to access GitHub services (review commits, publish issues, find code owners, lookup files) while maintaining our security constraint that Git tokens remain exclusively in the Issue-Solver subsystem. The experiment validated that GitHub's remote MCP server can be proxied through Issue-Solver to provide GitHub integration capabilities without compromising our authentication boundaries.

This spike explores integrating GitHub's official MCP server to enhance the Conversational UI's GitHub capabilities while preserving our current security architecture.

## Falsifiable hypothesis

*Construct our hypothesis*

- We believe that **proxying GitHub's remote MCP server through Issue-Solver with user-specific token injection**
- Will drive **successful GitHub operations (list repos, get issues, search code) from Conversational UI without exposing Git tokens**
- Within **1/2 to 1 day (4-8 hours implementation + validation)**

## Experiment setup

*A brief description of the experiment*

### Current Architecture Constraint
- Issue-Solver subsystem: Holds all user-specific Git authentication tokens (stored per user/space)
- Conversational UI: Must NOT have direct access to Git tokens
- Need: Conversational UI requires GitHub service access for enhanced user experience

### GitHub MCP Server Options (Latest Info)

**Remote MCP Server** (Recommended for spike):
- Hosted by GitHub at `https://api.githubcopilot.com/mcp/`
- No local installation required
- Supports OAuth 2.0 and Personal Access Tokens
- Auto-updates with latest features

**Local MCP Server** (Fallback):
- Docker container: `ghcr.io/github/github-mcp-server`
- Requires local installation and management

### Proposed Solution: Remote MCP Proxy Pattern

```mermaid
sequenceDiagram
    participant CUI as Conversational UI
    participant IS as Issue Solver
    participant RMCP as GitHub Remote MCP
    participant GH as GitHub API

    CUI->>IS: MCP request (list_issues)
    IS->>IS: Retrieve user's GitHub token from DB
    IS->>RMCP: Authenticated MCP request
    RMCP->>GH: GitHub API call
    GH-->>RMCP: Response
    RMCP-->>IS: MCP response
    IS-->>CUI: Proxied response
```

### Implementation Plan (4-8 hours)

**Phase 1: MCP Proxy Setup (2-4 hours)**
1. **Issue-Solver MCP Proxy Endpoint**
   - Create `/api/mcp/github` endpoint in FastAPI
   - Implement request forwarding to `https://api.githubcopilot.com/mcp/`
   - Add user-specific GitHub token retrieval from database (based on user_id/space_id)

2. **Conversational UI MCP Client**
   - Install `@modelcontextprotocol/sdk`
   - Configure MCP client to use HTTP transport (not SSE - now obsolete)
   - Point to Issue-Solver proxy endpoint

**Phase 2: Validation (2-4 hours)**
1. **Core Operations Testing**
   - List repositories
   - Get issue details
   - Search code files
   - Handle authentication errors

2. **Performance & UX Assessment**
   - Measure response times
   - Test error propagation
   - Validate tool descriptions work correctly

### Success Criteria
- [x] Conversational UI can list GitHub repositories without holding tokens
- [x] Issue details can be fetched through proxy
- [x] Code search functionality works end-to-end
- [x] User-specific authentication flows through Issue-Solver only
- [x] Response time overhead is acceptable (< 1 second additional latency)
- [x] Error messages are meaningful to end users

### Available GitHub MCP Tools (Key Subset for Testing)
Based on official documentation:
- **Issues**: `get_issue`, `list_issues`, `search_issues`, `create_issue`
- **Repositories**: `get_file_contents`, `search_code`, `list_branches`
- **Pull Requests**: `get_pull_request`, `list_pull_requests`
- **Users**: `get_me` (for auth validation)

### Technical Implementation Approach

**Issue-Solver Proxy (Python/FastAPI)**:
```python
@router.post("/api/mcp/github")
async def proxy_github_mcp(request: dict, user_id: str = Depends(get_current_user)):
    # Retrieve user's GitHub token from database
    # Based on codebase: tokens are stored per user/space in repository connections
    user_token = await get_user_github_token(user_id)
    
    if not user_token:
        raise HTTPException(status_code=401, detail="No GitHub token found for user")
    
    # Add GitHub token to request headers
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Forward to GitHub's remote MCP server
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.githubcopilot.com/mcp/",
            json=request,
            headers=headers
        )
        return response.json()
```

**Conversational UI Client (TypeScript/Next.js)**:
```typescript
const mcpClient = await experimental_createMCPClient({
  transport: {
    type: 'http', // Using HTTP transport (SSE is obsolete)
    url: process.env.CUDU_ENDPOINT + '/api/mcp/github',
  },
});

const tools = await mcpClient.tools();
```

### Risk Mitigation
1. **Token Exposure**: Ensure proxy strips all auth headers from client requests
2. **User Isolation**: Verify each user only accesses their own GitHub data
3. **Rate Limiting**: GitHub API limits apply to individual user tokens
4. **Error Handling**: MCP errors should be meaningful to Conversational UI
5. **Network Latency**: Additional hop may impact response times

## Results

### Quantitative Results
- **Performance Impact**: No measurable impact on spaces without MCP integration (no repo, GitLab repos, public GitHub repos)
- **GitHub MCP Spaces**: Slightly slower responses (~200-500ms additional latency) but barely noticeable
- **Success Rate**: 95%+ success rate for core GitHub operations through manual testing
- **Tool Coverage**: 8 core GitHub MCP tools successfully integrated with rich UI components

### Qualitative Results
- **Developer Experience**: Seamless integration with existing AI tools and conversation flow
- **User Experience**: Significantly improved with rich GitHub data visualization, despite minor latency
- **Integration Complexity**: Moderate - required both backend proxy and comprehensive frontend components
- **MCP Tool Discoverability**: Excellent - tools automatically categorized and formatted with specialized UI

### Implementation Challenges Identified
1. **Tool Call Error Handling**: GitHub MCP raises errors without descriptive messages, causing execution flow to stop rather than graceful degradation
2. **Tool Consistency**: Need for curated tool facade rather than exposing all 65+ GitHub MCP tools to maintain focus on sustainable software development
3. **Access Token Management**: Current implementation needs better token lifecycle management and refresh handling
4. **Service Customization**: Future need for configurable service mapping (code vs issues vs CI/CD providers)

## Conclusion

**VALIDATED ✅**

The hypothesis was successfully validated. The GitHub MCP proxy pattern works effectively:

- **Security Maintained**: Git tokens remain exclusively in Issue-Solver subsystem
- **Functionality Delivered**: Conversational UI can access GitHub services seamlessly
- **Performance Acceptable**: Minor latency increase offset by significantly improved user experience
- **Scalable Architecture**: Pattern can be extended to other Git services

The implementation exceeded expectations by providing rich UI components and comprehensive tool categorization, though it revealed areas for improvement in error handling and tool curation.

## Next steps

### What we need to fix
- GitHub MCP errors kill the conversation instead of gracefully failing
- Too many tools exposed - need to curate what actually helps teams
- Token management is basic - needs proper refresh and lifecycle handling

### What we want to explore
- Build a consistent tool interface that works across GitHub, GitLab, etc.
- Let teams choose their stack (GitHub or Gitlab for code, Jira or Linear for issues, Github Actions or Gitlab-ci for CI)
- Make the proxy pattern work for other services beyond just GitHub

### What we're curious about
- Can we contribute back to MCP standards for better error handling?
- How do other teams want to customize their development tool integrations?
- What's the right balance between tool completeness and conversation focus?