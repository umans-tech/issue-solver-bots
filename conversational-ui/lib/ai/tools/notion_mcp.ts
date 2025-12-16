import { experimental_createMCPClient as createMCPClient } from 'ai';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';

const NOTION_PROXY_PATH = '/mcp/notion/proxy';
const CACHE_TTL_MS = 5 * 60 * 1000;
const MAX_CACHE_SIZE = 100; // Limit cache growth
const MCP_REQUEST_TIMEOUT_MS = 30_000; // 30s timeout for MCP requests

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

// Evict stale entries to prevent unbounded cache growth
function evictStaleEntries() {
  const now = Date.now();
  const toDelete: string[] = [];

  // Convert to array for iteration compatibility
  const entries = Array.from(notionClientCache.entries());
  for (const [key, entry] of entries) {
    if (now - entry.fetchedAt > CACHE_TTL_MS) {
      toDelete.push(key);
      // Clean up MCP client connection
      entry.client.close().catch((err) => {
        console.error('[Notion MCP] Failed to close stale client:', err);
      });
    }
  }

  toDelete.forEach((key) => notionClientCache.delete(key));

  // If cache still too large, evict oldest entries
  if (notionClientCache.size > MAX_CACHE_SIZE) {
    const sortedEntries = Array.from(notionClientCache.entries()).sort(
      ([, a], [, b]) => a.fetchedAt - b.fetchedAt,
    );
    const excess = notionClientCache.size - MAX_CACHE_SIZE;
    for (let i = 0; i < excess; i++) {
      const [key, entry] = sortedEntries[i];
      notionClientCache.delete(key);
      entry.client.close().catch((err) => {
        console.error('[Notion MCP] Failed to close evicted client:', err);
      });
    }
  }
}

const noMCPClient = (error: unknown): MCPWrapper => ({
  client: {
    tools: async () => ({}) as any,
    close: async () => {
      /* noop */
    },
  } as unknown as MCPClient,
  activeTools: () => [],
  loadTools: async () => ({}),
  __error: error,
});

export async function notionMCPClient(
  userContext?: UserContext,
): Promise<MCPWrapper> {
  // Periodically clean stale cache entries
  evictStaleEntries();

  const cacheKey = userContext?.spaceId
    ? `${userContext.spaceId}:${userContext?.userId ?? 'anonymous'}`
    : null;

  if (cacheKey) {
    const cached = notionClientCache.get(cacheKey);
    if (cached && Date.now() - cached.fetchedAt < CACHE_TTL_MS) {
      return cached;
    } else if (cached) {
      // Remove expired entry and close connection
      notionClientCache.delete(cacheKey);
      cached.client.close().catch((err) => {
        console.error('[Notion MCP] Failed to close expired client:', err);
      });
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
    // Remove from cache on error to force refresh on next attempt
    if (cacheKey) {
      notionClientCache.delete(cacheKey);
    }
    return noMCPClient(error);
  }
}

async function createProxyClient(
  userContext?: UserContext,
): Promise<MCPWrapper> {
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

      // Wrap with timeout protection to prevent hung requests
      return Promise.race([
        super.send(request),
        new Promise((_, reject) =>
          setTimeout(
            () => reject(new Error('MCP request timeout')),
            MCP_REQUEST_TIMEOUT_MS,
          ),
        ),
      ]);
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
    .filter(
      ([name]) =>
        name.toLowerCase().includes('notion') ||
        name.toLowerCase().startsWith('page_'),
    )
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
