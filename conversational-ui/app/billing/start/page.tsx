'use client';

import { useEffect } from 'react';

function getCookie(name: string): string | null {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()!.split(';').shift() || null;
  return null;
}

export default function BillingStartPage() {
  useEffect(() => {
    const run = async () => {
      try {
        const raw = getCookie('pending_checkout');
        let plan: 'individual' | 'team' = 'individual';
        let cycle: 'monthly' | 'yearly' = 'monthly';
        if (raw) {
          try {
            const parsed = JSON.parse(decodeURIComponent(raw));
            if (parsed?.plan === 'individual' || parsed?.plan === 'team') plan = parsed.plan;
            if (parsed?.cycle === 'monthly' || parsed?.cycle === 'yearly') cycle = parsed.cycle;
          } catch {}
        }

        const res = await fetch('/api/billing/checkout', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ plan, cycle }),
        });
        if (res.status === 401) {
          window.location.href = `/register?plan=${plan}&cycle=${cycle}`;
          return;
        }
        const data = await res.json();
        if (data?.url) {
          window.location.href = data.url as string;
        } else {
          window.location.href = '/?billing=failed';
        }
      } catch {
        window.location.href = '/?billing=failed';
      }
    };
    run();
  }, []);

  return null;
}


