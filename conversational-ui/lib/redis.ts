import Redis from 'ioredis';

// ⏮️ Hot‑reload friendly in dev
const globalForRedis = global as unknown as { redis?: Redis };

export const redis =
  globalForRedis.redis ??
  new Redis(process.env.REDIS_URL as string, {
    connectTimeout: 5_000,
    maxRetriesPerRequest: 1,
    // Prevent connection exhaustion with explicit configuration
    enableReadyCheck: true,
    enableOfflineQueue: false, // Fail fast instead of queueing commands
    lazyConnect: false,
    keepAlive: 30000, // 30s keepalive to detect dead connections
    // Reconnection strategy with backoff
    retryStrategy(times: number) {
      const maxRetries = 3;
      if (times > maxRetries) {
        console.error('[Redis] Max connection retries exceeded');
        return null; // Stop retrying
      }
      const delay = Math.min(times * 200, 2000); // Max 2s backoff
      return delay;
    },
  });

if (process.env.NODE_ENV !== 'production') globalForRedis.redis = redis;
