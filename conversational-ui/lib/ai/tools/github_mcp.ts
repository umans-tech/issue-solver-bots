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

    // Use custom transport to connect to our Issue-Solver proxy
    const transport = new UserContextTransport(
        new URL(`${cuduEndpoint}/mcp/repositories/proxy`),
        {
            requestInit: {
                headers: {
                    'Content-Type': 'application/json'
                    // No Authorization header - proxy will handle token injection
                }
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
            "search_code",
            "get_file_contents",
            "list_repositories",
            "get_pull_request",
            "list_pull_requests"
        ],
    };
}