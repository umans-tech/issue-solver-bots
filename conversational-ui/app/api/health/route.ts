// app/api/health/route.ts
import { NextResponse } from 'next/server';
import { redis } from '@/lib/redis';
import { db } from '@/lib/db';
import { getControllerStats } from '@/lib/stream/controller-registry';
import { sql } from 'drizzle-orm';

export const runtime = 'nodejs';

export async function GET() {
  const checks: Record<string, any> = {
    status: 'ok',
    timestamp: new Date().toISOString(),
  };

  try {
    // Check Redis connectivity
    const redisPing = await Promise.race([
      redis.ping(),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('timeout')), 2000),
      ),
    ]);
    checks.redis = redisPing === 'PONG' ? 'healthy' : 'degraded';
  } catch (error) {
    checks.redis = 'unhealthy';
    checks.redisError = (error as Error).message;
  }

  try {
    // Check PostgreSQL connectivity
    await Promise.race([
      db.execute(sql`SELECT 1`),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('timeout')), 2000),
      ),
    ]);
    checks.postgres = 'healthy';
  } catch (error) {
    checks.postgres = 'unhealthy';
    checks.postgresError = (error as Error).message;
  }

  // Get stream controller metrics
  try {
    const controllerStats = getControllerStats();
    checks.controllers = {
      total: controllerStats.total,
      active: controllerStats.active,
      status:
        controllerStats.total > 500
          ? 'warning'
          : controllerStats.total > 900
            ? 'critical'
            : 'healthy',
    };
  } catch (error) {
    checks.controllers = 'error';
  }

  // Determine overall health status
  const isHealthy =
    checks.redis !== 'unhealthy' && checks.postgres !== 'unhealthy';

  return NextResponse.json(checks, {
    status: isHealthy ? 200 : 503,
  });
}
