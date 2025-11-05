'use client';

import { useEffect, useMemo, useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Badge } from '@/components/ui/badge';
import { CheckCircleFillIcon, AlertCircle, ClockRewind } from '@/components/icons';

interface NotionIntegrationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface NotionIntegrationDetails {
  connectedAt: string;
  workspaceId?: string | null;
  workspaceName?: string | null;
  botId?: string | null;
  processId: string;
  tokenExpiresAt?: string | null;
  hasMcpToken: boolean;
}

export function NotionIntegrationDialog({
  open,
  onOpenChange,
}: NotionIntegrationDialogProps) {
  const { data: session } = useSession();
  const router = useRouter();
  const spaceId = session?.user?.selectedSpace?.id ?? null;

  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [integration, setIntegration] = useState<NotionIntegrationDetails | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [didRefresh, setDidRefresh] = useState(false);

  const statusBadge = useMemo(() => {
    if (integration) {
      if (integration.hasMcpToken) {
        return (
          <Badge variant="outline" className="gap-1 text-xs">
            <CheckCircleFillIcon size={14} className="text-green-500" />
            Connected
          </Badge>
        );
      }
      return (
        <Badge variant="secondary" className="gap-1 text-xs">
          <AlertCircle size={14} />
          Authorization required
        </Badge>
      );
    }
    if (error) {
      return (
        <Badge variant="destructive" className="gap-1 text-xs">
          <AlertCircle size={14} />
          Error
        </Badge>
      );
    }
    return (
      <Badge variant="secondary" className="gap-1 text-xs">
        <ClockRewind size={14} />
        Not connected
      </Badge>
    );
  }, [integration, error]);

  useEffect(() => {
    if (!open) {
      setError(null);
      setDidRefresh(false);
      return;
    }

    if (!spaceId) {
      setError('Select a space to authorize Notion.');
      return;
    }

    setIsLoading(true);
    fetch(`/api/notion?spaceId=${spaceId}`, { cache: 'no-store' })
      .then(async (res) => {
        if (res.status === 404) {
          setIntegration(null);
          setError(null);
          return;
        }
        if (!res.ok) {
          const payload = await res.json().catch(() => ({}));
          throw new Error(payload?.error || 'Failed to load Notion integration');
        }
        const payload = await res.json();
        if (payload?.connected && payload.integration) {
          const details = payload.integration;
          setIntegration({
            connectedAt:
              details.connected_at ?? details.connectedAt ?? new Date().toISOString(),
            workspaceId: details.workspace_id ?? details.workspaceId ?? null,
            workspaceName: details.workspace_name ?? details.workspaceName ?? null,
            botId: details.bot_id ?? details.botId ?? null,
            processId: details.process_id ?? details.processId,
            tokenExpiresAt: details.token_expires_at ?? details.tokenExpiresAt ?? null,
            hasMcpToken:
              details.has_mcp_token ?? details.hasMcpToken ?? details.hasMcp ?? false,
          });
          setError(null);
          if (!didRefresh && details.hasMcpToken) {
            setDidRefresh(true);
            router.refresh();
          }
        } else {
          setIntegration(null);
        }
      })
      .catch((err: Error) => {
        console.error('Unable to load Notion integration', err);
        setError(err.message);
        setIntegration(null);
      })
      .finally(() => setIsLoading(false));
  }, [open, spaceId, didRefresh, router]);

  const handleConnect = async () => {
    if (!spaceId) {
      toast.error('Select a space before authorizing Notion.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      const response = await fetch('/api/notion/oauth/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          spaceId,
          returnPath: '/integrations/notion/callback',
        }),
      });

      const result = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(result?.error || 'Failed to start the Notion connection');
      }
      if (result?.authorizeUrl) {
        window.location.href = result.authorizeUrl;
      } else {
        throw new Error('Missing authorization URL from server.');
      }
    } catch (err: any) {
      console.error('Failed to initiate Notion authorization', err);
      toast.error(err.message || 'Failed to start the Notion connection');
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const actionLabel = integration?.hasMcpToken
    ? 'Reconnect Notion'
    : 'Connect Notion';

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6">
        <SheetHeader>
          <SheetTitle>Connect Notion</SheetTitle>
          <SheetDescription>
            Bring your Notion workspace into this space so everyone can pull rich context into conversations, capture better tickets, and publish polished docs—without leaving Umans.
          </SheetDescription>
        </SheetHeader>

        <div className="space-y-4 text-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Status</p>
              {integration?.connectedAt && (
                <p className="text-xs text-muted-foreground">
                  Connected {new Date(integration.connectedAt).toLocaleString()}
                </p>
              )}
            </div>
            {statusBadge}
          </div>

          {integration?.workspaceName && (
            <div className="rounded-md border bg-muted/20 p-3">
              <p className="text-sm font-medium">Workspace</p>
              <p className="text-sm text-muted-foreground">
                {integration.workspaceName} ({integration.workspaceId ?? 'unknown'})
              </p>
            </div>
          )}

          {integration?.botId && (
            <div className="rounded-md border bg-muted/20 p-3">
              <p className="text-sm font-medium">Connection ID</p>
              <p className="text-sm text-muted-foreground">{integration.botId}</p>
            </div>
          )}

          <div className="space-y-2">
            {!integration?.hasMcpToken && (
              <p className="text-xs text-muted-foreground">
                Select “{actionLabel}” to approve the Notion consent screen.
              </p>
            )}
            <p className="text-xs text-muted-foreground">
              By connecting, you let every teammate and Umans agent in this space search your Notion workspace for context, draft better tickets, and update pages when you ask.
            </p>
          </div>
        </div>

        <SheetFooter className="flex flex-col gap-3 sm:flex-row sm:justify-between sm:gap-2">
          {error && (
            <div className="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <div className="flex w-full flex-col gap-3 sm:flex-row sm:items-center sm:gap-2">
            <Button
              type="button"
              onClick={handleConnect}
              disabled={isSubmitting || isLoading || !spaceId}
              className="w-full sm:w-auto"
            >
              {isSubmitting ? 'Redirecting…' : actionLabel}
            </Button>
          </div>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
