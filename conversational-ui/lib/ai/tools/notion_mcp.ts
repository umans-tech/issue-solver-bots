import { experimental_createMCPClient as createMCPClient } from 'ai';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';

const NOTION_PROXY_PATH = '/mcp/notion/proxy';
const CACHE_TTL_MS = 5 * 60 * 1000;

type UserContext = { userId?: string; spaceId?: string } | undefined;

type MCPClient = Awaited<ReturnType<typeof createMCPClient>>;

type MCPWrapper = {
  client: MCPClient;
  activeTools: () => string[];
  loadTools: () => Promise<Record<string, unknown>>;
  persistent?: boolean;
  __error?: unknown;
};

type CachedEntry = MCPWrapper & { fetchedAt: number };

const notionClientCache = new Map<string, CachedEntry>();

const noMCPClient = (error: unknown): MCPWrapper => ({
  client: {
    tools: async () => ({} as any),
    close: async () => {
      /* noop */
    },
  } as unknown as MCPClient,
  activeTools: () => [],
  loadTools: async () => ({}),
  __error: error,
});

export async function notionMCPClient(userContext?: UserContext): Promise<MCPWrapper> {
  const cacheKey = userContext?.spaceId
    ? `${userContext.spaceId}:${userContext?.userId ?? 'anonymous'}`
    : null;

  if (cacheKey) {
    const cached = notionClientCache.get(cacheKey);
    if (cached && Date.now() - cached.fetchedAt < CACHE_TTL_MS) {
      return cached;
    }
  }

  try {
    const wrapper = await createProxyClient(userContext);
    if (cacheKey) {
      notionClientCache.set(cacheKey, { ...wrapper, fetchedAt: Date.now() });
    }
    return wrapper;
  } catch (error) {
    console.error('[Notion MCP] failed to initialise client:', error);
    return noMCPClient(error);
  }
}

async function createProxyClient(userContext?: UserContext): Promise<MCPWrapper> {
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
  const fullToolMap = await client.tools();
  const filteredEntries = Object.entries(fullToolMap ?? {})
    .filter(([name]) => name.toLowerCase().includes('notion') || name.toLowerCase().startsWith('page_'))
    .slice(0, 16);

  const toolMap = Object.fromEntries(filteredEntries);
  const toolNames = filteredEntries.map(([name]) => name);

  return {
    client,
    activeTools: () => toolNames,
    loadTools: async () => toolMap,
    persistent: true,
  };
}
