'use client';

import { useEffect, useState } from 'react';
import { Check } from 'lucide-react';
import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';

type Cycle = 'monthly' | 'yearly';

const plans = [
  {
    name: 'Solo',
    description: 'For solo founders and indie hackers',
    features: [
      '200 monthly agent credits',
      'Extended runs with GPT-5, Claude Sonnet & Claude Code',
      'Personal workspace with persistent context & docs',
    ],
    cta: 'Get started',
    planKey: 'solo' as const,
    pricing: {
      monthly: { amount: '$24', descriptor: 'per user / month' },
      yearly: { amount: '$19', descriptor: 'per user / month' },
    },
  },
  {
    name: 'Pro',
    description: 'Built for product pros that ship together',
    features: [
      '600 shared monthly agent credits',
      'Shared spaces with cross-conversation memory',
      'Seats for up to 5 collaborators (per-user pricing)',
    ],
    cta: 'Get started',
    planKey: 'pro' as const,
    popular: true,
    pricing: {
      monthly: { amount: '$49', descriptor: 'per user / month' },
      yearly: { amount: '$41', descriptor: 'per user / month' },
    },
  },
  {
    name: 'Enterprise',
    description: 'Tailored to your engineering org',
    features: [
      'Custom credit pools & scaling guarantees',
      'Dedicated environment profiles per pro',
      'White-glove enablement + shared roadmap planning',
    ],
    cta: 'Contact us',
    planKey: 'enterprise' as const,
    pricing: {
      monthly: { amount: 'Flexible billing', descriptor: '' },
      yearly: { amount: 'Flexible billing', descriptor: '' },
    },
  },
] as const;

export function PricingDialog({ children }: { children?: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const [cycle, setCycle] = useState<Cycle>('monthly');

  useEffect(() => {
    const handler = () => setOpen(true);
    if (typeof window !== 'undefined') {
      window.addEventListener('open-pricing-dialog', handler as EventListener);
    }
    return () => {
      if (typeof window !== 'undefined') {
        window.removeEventListener('open-pricing-dialog', handler as EventListener);
      }
    };
  }, []);

  const startCheckout = async (planKey: 'solo' | 'pro') => {
    try {
      const res = await fetch('/api/billing/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan: planKey, cycle }),
      });
      if (res.status === 401) {
        document.cookie = `pending_checkout=${encodeURIComponent(JSON.stringify({ plan: planKey, cycle }))}; Path=/; Max-Age=3600; SameSite=Lax`;
        window.location.href = `/register?plan=${planKey}&cycle=${cycle}`;
        return;
      }
      const data = await res.json();
      if (data?.url) {
        window.location.href = data.url as string;
      }
    } catch {}
  };

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      {children ? <SheetTrigger asChild>{children}</SheetTrigger> : null}
      <SheetContent side="right" className="w-full sm:max-w-lg p-0 flex flex-col">
        <SheetHeader className="px-6 pt-6">
          <SheetTitle>Pricing</SheetTitle>
        </SheetHeader>

        <div className="mt-4 mb-3 flex justify-center px-6">
          <div className="inline-flex items-center rounded-full border border-border/60 bg-card/80 p-1 text-sm font-medium shadow-sm backdrop-blur">
            {(['monthly', 'yearly'] as const).map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setCycle(c)}
                className={`rounded-full px-4 py-2 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 ${
                  cycle === c ? 'bg-primary text-primary-foreground shadow-md' : 'text-muted-foreground hover:text-foreground hover:bg-muted/30'
                }`}
              >
                {c === 'monthly' ? 'Monthly' : 'Yearly'}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-6 pb-6 space-y-4">
          {plans.map((p) => {
            const price = p.pricing[cycle];
            const isEnterprise = p.planKey === 'enterprise';
            return (
              <div key={p.name} className={`relative rounded-2xl border p-5 bg-card/80 ${p.planKey === 'pro' ? 'border-primary/60 ring-1 ring-primary/20 from-primary/5 shadow' : 'border-border/50'}`}>
                {p.planKey === 'pro' && (
                  <span className="pointer-events-none absolute right-4 top-4 inline-flex items-center rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary shadow-sm">
                    Most popular
                  </span>
                )}
                <div className="space-y-1">
                  <div className="text-lg font-bold">{p.name}</div>
                  <div className="text-xs text-muted-foreground">{p.description}</div>
                </div>
                <div className="mt-3 flex items-baseline gap-2">
                  <div className={`${isEnterprise ? 'text-base' : 'text-2xl whitespace-nowrap'} font-bold`}>{price.amount}</div>
                  {!isEnterprise && <div className="text-xs text-muted-foreground whitespace-nowrap">{price.descriptor}</div>}
                </div>
                <ul className="mt-3 space-y-1.5 text-xs text-muted-foreground">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-start gap-2">
                      <Check className="h-3.5 w-3.5 mt-0.5 text-primary" />
                      <span className="leading-relaxed">{f}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-4">
                  {p.planKey === 'enterprise' ? (
                    <Link href="mailto:contact@umans.ai" className="inline-flex w-full items-center justify-center rounded-md border border-border/60 bg-background px-6 py-2 text-sm font-semibold hover:border-border">{p.cta}</Link>
                  ) : (
                    <Button className="w-full" onClick={() => startCheckout(p.planKey)}>{p.cta}</Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </SheetContent>
    </Sheet>
  );
}


