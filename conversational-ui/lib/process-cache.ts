const DEFAULT_TTL_MS = 5000;
const MAX_CACHE_SIZE = 1000; // Limit cache to 1000 entries

type CachedEntry = {
  data: any;
  expiresAt: number;
  lastAccessed: number;
};

const cache = new Map<string, CachedEntry>();

/**
 * Evict expired and least-recently-used entries when cache is full
 */
function evictIfNeeded() {
  // First, remove all expired entries
  const now = Date.now();
  for (const [key, entry] of cache.entries()) {
    if (entry.expiresAt <= now) {
      cache.delete(key);
    }
  }

  // If still over limit, remove least-recently-used entries
  if (cache.size >= MAX_CACHE_SIZE) {
    const entries = Array.from(cache.entries());
    entries.sort((a, b) => a[1].lastAccessed - b[1].lastAccessed);
    const toRemove = Math.max(1, Math.floor(MAX_CACHE_SIZE * 0.1)); // Remove 10% of cache
    for (let i = 0; i < toRemove && entries[i]; i++) {
      cache.delete(entries[i][0]);
    }
  }
}

export function getCachedProcess(processId: string): any | null {
  const cached = cache.get(processId);
  if (!cached) return null;
  if (cached.expiresAt <= Date.now()) {
    cache.delete(processId);
    return null;
  }
  // Update last accessed time for LRU
  cached.lastAccessed = Date.now();
  return cached.data;
}

export function setCachedProcess(processId: string, data: any, ttlMs: number = DEFAULT_TTL_MS) {
  evictIfNeeded();
  cache.set(processId, {
    data,
    expiresAt: Date.now() + ttlMs,
    lastAccessed: Date.now(),
  });
}
