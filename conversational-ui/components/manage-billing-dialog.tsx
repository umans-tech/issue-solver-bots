'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';

import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';

const FALLBACK_PORTAL_URL =
  'https://dashboard.stripe.com/login?redirect=%2Finvoices';
const FALLBACK_SUPPORT_EMAIL = 'billing@umans.ai';

export function ManageBillingDialog({
  children,
}: { children?: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const [runtimeConfig, setRuntimeConfig] = useState<any>(() => {
    if (typeof window === 'undefined') return null;
    return (globalThis as any).__RUNTIME_CONFIG__ || null;
  });

  useEffect(() => {
    const handler = () => setOpen(true);
    if (typeof window !== 'undefined') {
      window.addEventListener('open-manage-billing', handler as EventListener);
      setRuntimeConfig((globalThis as any).__RUNTIME_CONFIG__ || null);
    }
    return () => {
      if (typeof window !== 'undefined') {
        window.removeEventListener(
          'open-manage-billing',
          handler as EventListener,
        );
      }
    };
  }, []);

  const portalUrl = useMemo(() => {
    return runtimeConfig?.STRIPE_BILLING_PORTAL_URL || FALLBACK_PORTAL_URL;
  }, [runtimeConfig]);

  const supportEmail = useMemo(() => {
    return runtimeConfig?.UMANS_BILLING_SUPPORT_EMAIL || FALLBACK_SUPPORT_EMAIL;
  }, [runtimeConfig]);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      {children ? <SheetTrigger asChild>{children}</SheetTrigger> : null}
      <SheetContent
        side="right"
        className="w-full sm:max-w-md p-0 flex flex-col"
      >
        <SheetHeader className="px-6 pt-6">
          <SheetTitle>Manage billing</SheetTitle>
          <SheetDescription>
            We are rolling out a richer billing experience soon. Jump to the
            customer portal to review invoices or update payment details, or
            reach out to our team directly.
          </SheetDescription>
        </SheetHeader>

        <div className="px-6 mt-6 space-y-3 text-sm text-muted-foreground">
          <p>
            Billing portal access requires the email you used to subscribe. If
            you do not see your workspace&apos;s invoices, contact us and
            we&apos;ll help right away.
          </p>
        </div>

        <div className="mt-auto flex flex-col gap-3 px-6 pb-6 pt-8">
          <Button asChild className="w-full">
            <Link href={portalUrl} target="_blank" rel="noreferrer">
              Open invoices portal
            </Link>
          </Button>
          <Button variant="outline" asChild className="w-full">
            <Link href={`mailto:${supportEmail}`}>Email billing support</Link>
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
