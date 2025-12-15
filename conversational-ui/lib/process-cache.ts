const DEFAULT_TTL_MS = 5000;

type CachedEntry = {
  data: any;
  expiresAt: number;
};

const cache = new Map<string, CachedEntry>();

export function getCachedProcess(processId: string): any | null {
  const cached = cache.get(processId);
  if (!cached) return null;
  if (cached.expiresAt <= Date.now()) {
    cache.delete(processId);
    return null;
  }
  return cached.data;
}

export function setCachedProcess(
  processId: string,
  data: any,
  ttlMs: number = DEFAULT_TTL_MS,
) {
  cache.set(processId, {
    data,
    expiresAt: Date.now() + ttlMs,
  });
}
