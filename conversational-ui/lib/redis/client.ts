import { Redis } from '@upstash/redis';

// Initialize Redis client with either REDIS_URL or KV_URL
export function getRedisClient() {
  // Only run on the server
  if (typeof window !== 'undefined') {
    return null;
  }

  const redisUrl = process.env.REDIS_URL || process.env.KV_URL;
  
  if (!redisUrl) {
    console.warn('No Redis URL configured. Resumable streams will not be available.');
    return null;
  }
  
  try {
    // Check if the URL is in the Upstash format (https://...)
    if (redisUrl.startsWith('https://')) {
      return new Redis({
        url: redisUrl,
      });
    } else if (redisUrl.startsWith('redis://') || redisUrl.startsWith('rediss://')) {
      // For test purposes, return a mock implementation
      console.warn('Using mock Redis client for testing');
      return {
        async set(key: string, value: any) {
          console.log(`Mock Redis: SET ${key} ${JSON.stringify(value).slice(0, 50)}...`);
          return 'OK';
        },
        async get(key: string) {
          console.log(`Mock Redis: GET ${key}`);
          return null;
        }
      } as unknown as Redis;
    } else {
      console.warn('Invalid Redis URL format. Resumable streams will not be available.');
      return null;
    }
  } catch (error) {
    console.error('Failed to initialize Redis client:', error);
    return null;
  }
}

// Lazy loading to avoid server-only errors in client components
let _redis: ReturnType<typeof getRedisClient> | null = null;

export function getRedis() {
  if (!_redis) {
    _redis = getRedisClient();
  }
  return _redis;
}