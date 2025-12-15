import { NextResponse } from 'next/server';
import { redis } from '@/lib/redis';

export const runtime = 'nodejs'; // ← Edge can’t open raw TCP sockets

export async function GET() {
  try {
    const pong = await redis.ping(); // "PONG" on success
    return NextResponse.json({ ok: pong === 'PONG' });
  } catch (err) {
    return NextResponse.json(
      { ok: false, error: (err as Error).message },
      { status: 500 },
    );
  }
}
