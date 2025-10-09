'use client';

import { useEffect, useMemo, useState } from 'react';
import { useSession } from 'next-auth/react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
import { ExternalLink } from 'lucide-react';

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
}

export function NotionIntegrationDialog({
  open,
  onOpenChange,
}: NotionIntegrationDialogProps) {
  const { data: session } = useSession();
  const spaceId = session?.user?.selectedSpace?.id ?? null;

  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [accessToken, setAccessToken] = useState('');
  const [integration, setIntegration] = useState<NotionIntegrationDetails | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);
  const [rotateMode, setRotateMode] = useState(false);

  const openNotionIntegrationSettings = () => {
    window.open('https://www.notion.so/my-integrations', '_blank', 'noopener,noreferrer');
  };

  const statusBadge = useMemo(() => {
    if (integration) {
      return (
        <Badge variant="outline" className="gap-1 text-xs">
          <CheckCircleFillIcon size={14} className="text-green-500" />
          Connected
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
      setAccessToken('');
      setRotateMode(false);
      setError(null);
      return;
    }

    if (!spaceId) {
      setError('Select a space to connect Notion.');
      return;
    }

    setIsLoading(true);
    fetch(`/api/notion?spaceId=${spaceId}`, { cache: 'no-store' })
      .then(async (res) => {
        if (!res.ok) {
          if (res.status === 404) {
            setIntegration(null);
            setError(null);
            return;
          }
          const payload = await res.json().catch(() => ({}));
          throw new Error(payload?.error || 'Failed to load Notion integration');
        }
        const payload = await res.json();
        if (payload?.connected && payload.integration) {
          const details = payload.integration;
          setIntegration({
            connectedAt: details.connected_at ?? details.connectedAt ?? new Date().toISOString(),
            workspaceId: details.workspace_id ?? null,
            workspaceName: details.workspace_name ?? null,
            botId: details.bot_id ?? null,
            processId: details.process_id,
          });
          setError(null);
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
  }, [open, spaceId]);

  const handleConnect = async () => {
    if (!accessToken.trim()) {
      toast.error('Provide a Notion integration token.');
      return;
    }
    if (!spaceId) {
      toast.error('Select a space before connecting Notion.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      const response = await fetch('/api/notion', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ accessToken, spaceId }),
      });

      const result = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(result?.error || 'Failed to connect Notion');
      }

      toast.success('Notion integration connected');
      setIntegration({
        connectedAt: result.connected_at ?? result.connectedAt ?? new Date().toISOString(),
        workspaceId: result.workspace_id ?? null,
        workspaceName: result.workspace_name ?? null,
        botId: result.bot_id ?? null,
        processId: result.process_id,
      });
      setAccessToken('');
      setRotateMode(false);
    } catch (err: any) {
      console.error('Failed to connect Notion', err);
      toast.error(err.message || 'Failed to connect Notion');
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRotate = async () => {
    if (!accessToken.trim()) {
      toast.error('Provide a new Notion token before rotating.');
      return;
    }
    if (!spaceId) {
      toast.error('Select a space before rotating the token.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      const response = await fetch('/api/notion', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ accessToken, spaceId }),
      });

      const result = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(result?.error || 'Failed to rotate Notion token');
      }

      toast.success('Notion token rotated');
      setAccessToken('');
      setRotateMode(false);
      setIntegration((current) =>
        current
          ? {
              ...current,
              workspaceId: result.workspace_id ?? current.workspaceId,
              workspaceName: result.workspace_name ?? current.workspaceName,
              botId: result.bot_id ?? current.botId,
            }
          : current,
      );
    } catch (err: any) {
      console.error('Failed to rotate Notion token', err);
      toast.error(err.message || 'Failed to rotate Notion token');
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const actionHandler =
    integration && !rotateMode
      ? () => setRotateMode(true)
      : integration && rotateMode
        ? handleRotate
        : handleConnect;
  const actionLabel = integration
    ? rotateMode
      ? 'Confirm rotation'
      : 'Rotate token'
    : 'Connect Notion';

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col gap-6">
        <SheetHeader>
          <SheetTitle>Connect Notion</SheetTitle>
          <SheetDescription>
            Securely connect your Notion workspace so MCP tools can read structured content when you need documentation context.
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
                {integration.workspaceName}
                {integration.workspaceId ? ` (${integration.workspaceId})` : ''}
              </p>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="notion-token">Notion integration token</Label>
            <Input
              id="notion-token"
              type="password"
              placeholder="secret_..."
              value={accessToken}
              disabled={isSubmitting}
              onChange={(event) => setAccessToken(event.target.value)}
            />
            <div className="space-y-1 text-xs text-muted-foreground">
              <div className="flex flex-wrap items-center gap-2">
                <span>Generate a token from your Notion integration settings.</span>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-6 px-2 text-xs"
                  onClick={openNotionIntegrationSettings}
                  disabled={isSubmitting}
                >
                  <ExternalLink className="mr-1 h-3 w-3" />
                  Open Notion
                </Button>
              </div>
              <p>The token stays on the server side and is encrypted at rest.</p>
            </div>
          </div>

          {error && (
            <div className="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}
        </div>

        <SheetFooter className="flex flex-col gap-2 sm:flex-row sm:justify-between">
          <Button
            variant="outline"
            onClick={() => {
              setRotateMode(false);
              setAccessToken('');
              onOpenChange(false);
            }}
            disabled={isSubmitting}
          >
            Close
          </Button>

          <Button
            onClick={actionHandler}
            disabled={isSubmitting || isLoading || !spaceId}
          >
            {isSubmitting ? 'Saving…' : actionLabel}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
