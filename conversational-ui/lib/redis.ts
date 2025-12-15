import Redis from 'ioredis';

// ⏮️ Hot‑reload friendly in dev
const globalForRedis = global as unknown as { redis?: Redis };

export const redis =
  globalForRedis.redis ??
  new Redis(process.env.REDIS_URL as string, {
    connectTimeout: 5_000,
    maxRetriesPerRequest: 1,
  });

if (process.env.NODE_ENV !== 'production') globalForRedis.redis = redis;
