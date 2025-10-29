
'use client';

import { Suspense, useEffect, useMemo } from 'react';
import { useSearchParams } from 'next/navigation';

import { Button } from '@/components/ui/button';
import { CheckCircleFillIcon, AlertCircle } from '@/components/icons';

function closeWindowFallback() {
  if (window.opener) {
    window.close();
  } else {
    window.location.href = '/';
  }
}

export default function NotionCallbackPage() {
  return (
    <Suspense fallback={<CallbackFallback />}>
      <NotionCallbackContent />
    </Suspense>
  );
}

function NotionCallbackContent() {
  const searchParams = useSearchParams();
  const status = searchParams.get('status');
  const error = searchParams.get('error');
  const workspaceId = searchParams.get('workspaceId');

  const { title, description, Icon, iconClass } = useMemo(() => {
    if (status === 'success') {
      return {
        title: 'Notion connected',
        description:
          'You can now return to Issue Solver and refresh the integration dialog.',
        Icon: CheckCircleFillIcon,
        iconClass: 'text-green-500',
      };
    }

    return {
      title: 'Notion connection failed',
      description:
        error ??
        'We could not verify the Notion authorization. Close this window and try again.',
      Icon: AlertCircle,
      iconClass: 'text-destructive',
    };
  }, [status, error]);

  useEffect(() => {
    if (status === 'success') {
      const timer = window.setTimeout(() => {
        if (window.opener) {
          window.close();
        }
      }, 2000);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [status]);

  const IconComponent = Icon;

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background px-6 py-12 text-center">
      <div className="flex flex-col items-center gap-3">
        <IconComponent size={42} className={iconClass} />
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          <p className="mt-2 max-w-md text-sm text-muted-foreground">{description}</p>
          {status === 'success' && workspaceId && (
            <p className="mt-3 text-xs text-muted-foreground">
              Workspace ID: <span className="font-mono">{workspaceId}</span>
            </p>
          )}
        </div>
      </div>

      <Button type="button" onClick={closeWindowFallback} variant="outline">
        Close window
      </Button>
    </div>
  );
}

function CallbackFallback() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6 py-12 text-center text-sm text-muted-foreground">
      Processing Notion authorization…
    </div>
  );
}
