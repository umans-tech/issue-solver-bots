import Redis from 'ioredis';

// ⏮️ Hot‑reload friendly in dev
const globalForRedis = global as unknown as { redis?: Redis };

export const redis =
  globalForRedis.redis ??
  new Redis(process.env.REDIS_URL as string, {
    connectTimeout: 10_000,
    maxRetriesPerRequest: 3,
    retryStrategy(times) {
      const delay = Math.min(times * 50, 2000);
      return delay;
    },
    reconnectOnError(err) {
      const targetError = 'READONLY';
      if (err.message.includes(targetError)) {
        // Reconnect on READONLY errors (failover scenarios)
        return true;
      }
      return false;
    },
    enableReadyCheck: true,
    enableOfflineQueue: true,
    lazyConnect: false,
    keepAlive: 30000,
    family: 0, // IPv4 or IPv6 auto-selection
    autoResubscribe: true,
    autoResendUnfulfilledCommands: true,
  });

if (process.env.NODE_ENV !== 'production') globalForRedis.redis = redis;
