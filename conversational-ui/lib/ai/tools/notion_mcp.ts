import { experimental_createMCPClient as createMCPClient } from 'ai';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';

const NOTION_PROXY_PATH = '/mcp/notion/proxy';

export async function notionMCPClient(userContext?: { userId?: string; spaceId?: string }) {
  try {
    return await createProxyClient(userContext);
  } catch (error) {
    console.error('[Notion MCP] failed to initialise client:', error);
    return noMCPClient(error);
  }
}

const noMCPClient = (error: unknown) => ({
  client: {
    tools: async () => ({}),
    close: () => {
      /* noop */
    },
  },
  activeTools: () => [],
  __error: error,
});

async function createProxyClient(userContext?: { userId?: string; spaceId?: string }) {
  const cuduEndpoint = process.env.CUDU_ENDPOINT;
  if (!cuduEndpoint) {
    throw new Error('CUDU_ENDPOINT not configured for Notion MCP integration');
  }

  class UserContextTransport extends StreamableHTTPClientTransport {
    async send(request: any): Promise<any> {
      if (userContext?.userId && userContext?.spaceId) {
        request.meta = {
          ...request.meta,
          user_id: userContext.userId,
          space_id: userContext.spaceId,
        };
      }
      return super.send(request);
    }
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (userContext?.userId) {
    headers['X-User-ID'] = userContext.userId;
  }

  const transport = new UserContextTransport(
    new URL(`${cuduEndpoint}${NOTION_PROXY_PATH}`),
    {
      requestInit: {
        headers,
      },
    },
  );

  const client = await createMCPClient({ transport });
  const toolMap = await client.tools();
  const toolNames = Object.keys(toolMap ?? {});
  if (process.env.NODE_ENV !== 'production') {
    console.log('[Notion MCP] tools discovered:', toolNames);
  }

  return {
    client,
    activeTools: () => toolNames,
  };
}
