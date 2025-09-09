import {experimental_createMCPClient as createMCPClient} from "ai";
import {StreamableHTTPClientTransport} from '@modelcontextprotocol/sdk/client/streamableHttp.js';

export async function codeRepositoryMCPClient(userContext?: { userId?: string; spaceId?: string }) {
    try {
        return await createProxyMCPClient(userContext)
    } catch (error) {
        return noMCPClient(error)
    }
}

const noMCPClient = (error: any) => ({
    client: {
        tools: async () => ({}),
        close: () => {
        }
    },
    activeTools: () => [],
})

const createProxyMCPClient = async (userContext?: { userId?: string; spaceId?: string }) => {
    // Get the CUDU API endpoint from environment variables
    const cuduEndpoint = process.env.CUDU_ENDPOINT;

    if (!cuduEndpoint) {
        throw new Error('CUDU_ENDPOINT not configured for GitHub MCP integration');
    }

    // Create custom transport that injects user context into requests
    class UserContextTransport extends StreamableHTTPClientTransport {
        async send(request: any): Promise<any> {
            // Inject user context into the request if available
            if (userContext?.userId && userContext?.spaceId) {
                request.meta = {
                    ...request.meta,
                    user_id: userContext.userId,
                    space_id: userContext.spaceId
                };
            }
            return super.send(request);
        }
    }

    // Prepare headers with user context
    const headers: Record<string, string> = {
        'Content-Type': 'application/json'
        // No Authorization header - proxy will handle token injection
    };

    // Add user ID header if available
    if (userContext?.userId) {
        headers['X-User-ID'] = userContext.userId;
    }

    // Use custom transport to connect to our Issue-Solver proxy
    const transport = new UserContextTransport(
        new URL(`${cuduEndpoint}/mcp/repositories/proxy`),
        {
            requestInit: {
                headers
            }
        }
    );

    const mcpClient = await createMCPClient({
        transport,
    });

    return {
        client: mcpClient,
        activeTools: () => [
            "get_me",
            "list_issues",
            "get_issue",
            "create_issue",
            "add_issue_comment",
            "update_issue",
            "search_code",
            "search_repositories",
            "get_file_contents",
            "get_pull_request",
            "list_pull_requests",
            "get_pull_request_files",
            "get_pull_request_diff",
            "get_issue_comments",
            "create_pull_request",
            "create_and_submit_pull_request_review",
            "list_commits",
            "get_commit",
            "list_workflow_runs",
            "get_workflow_run_logs",
            "list_code_scanning_alerts"
        ],
    };
}