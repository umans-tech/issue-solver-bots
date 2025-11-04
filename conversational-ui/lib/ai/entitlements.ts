import { startOfDay, startOfMonth } from 'date-fns';
import { getTokenUsageByUser } from '@/lib/db/queries';

type PlanKey = 'free' | 'solo' | 'pro' | 'enterprise' | string;

type Limits = {
  dailyCompletions?: number;
  monthlyCompletions?: number;
};

const PLAN_LIMITS: Record<string, Limits> = {
  free: { dailyCompletions: 125, monthlyCompletions: 150 },
  solo: { monthlyCompletions: 200 },
  pro: { monthlyCompletions: 600 },
  enterprise: {}, // unlimited
};

export type EntitlementResult = {
  ok: boolean;
  plan: PlanKey;
  usedToday: number;
  limitToday?: number;
  usedThisMonth: number;
  limitMonth?: number;
  reason?: string;
  retryAt?: string; // ISO when the limit resets for user messaging
};

export async function checkChatEntitlements({
  userId,
  plan,
}: {
  userId: string;
  plan: PlanKey;
}): Promise<EntitlementResult> {
  const limits = PLAN_LIMITS[plan] ?? PLAN_LIMITS.free;

  // Count completions from token usage rows. Each assistant completion records one row.
  const rows = await getTokenUsageByUser(userId);
  const today = startOfDay(new Date()).getTime();
  const month = startOfMonth(new Date()).getTime();

  let usedToday = 0;
  let usedThisMonth = 0;
  for (const r of rows) {
    const t = new Date((r as any).createdAt ?? (r as any).created_at ?? Date.now()).getTime();
    if (t >= month) usedThisMonth += 1;
    if (t >= today) usedToday += 1;
  }

  const withinDaily =
    limits.dailyCompletions === undefined || usedToday < (limits.dailyCompletions ?? Infinity);
  const withinMonthly =
    limits.monthlyCompletions === undefined || usedThisMonth < (limits.monthlyCompletions ?? Infinity);

  return {
    ok: withinDaily && withinMonthly,
    plan,
    usedToday,
    limitToday: limits.dailyCompletions,
    usedThisMonth,
    limitMonth: limits.monthlyCompletions,
    reason: !withinDaily
      ? 'daily-limit'
      : !withinMonthly
        ? 'monthly-limit'
        : undefined,
    retryAt: !withinDaily
      ? new Date(startOfDay(new Date()).getTime() + 24 * 60 * 60 * 1000).toISOString()
      : !withinMonthly
        ? new Date(startOfMonth(new Date()).setMonth(new Date().getMonth() + 1)).toISOString()
        : undefined,
  };
}


