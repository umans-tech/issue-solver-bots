'use client';

import { useEffect, useState } from 'react';
import { AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogFooter } from '@/components/ui/alert-dialog';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { ShellEditor } from '@/components/shell-editor';

interface EnvironmentSetupDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  knowledgeBaseId: string | undefined;
  onSuccess?: (data: { environment_id: string; process_id?: string }) => void;
}

export function EnvironmentSetupDialog({ open, onOpenChange, knowledgeBaseId, onSuccess }: EnvironmentSetupDialogProps) {
  const [globalSetup, setGlobalSetup] = useState('');
  const [projectSetup, setProjectSetup] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingPrefill, setIsLoadingPrefill] = useState(false);
  const [dirtyGlobal, setDirtyGlobal] = useState(false);
  const [dirtyProject, setDirtyProject] = useState(false);

  const canSubmit = !!knowledgeBaseId && (globalSetup.trim().length > 0 || projectSetup.trim().length > 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!knowledgeBaseId) return;
    if (!canSubmit) return;

    setIsSubmitting(true);
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 15000);

      const res = await fetch('/api/repo/environments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          knowledgeBaseId: knowledgeBaseId,
          ...(globalSetup.trim() ? { global: globalSetup.trim() } : {}),
          ...(projectSetup.trim() ? { project: projectSetup.trim() } : {}),
        }),
        signal: controller.signal,
      });
      clearTimeout(timeout);

      let data: any = null;
      try {
        data = await res.json();
      } catch {
        // ignore body parse errors
      }
      if (!res.ok) {
        const detail = (data && (data.detail || data.error)) || 'Failed to save environment';
        toast.error(detail);
        return;
      }

      toast.success('Environment saved');
      onSuccess?.({ environment_id: data.environment_id, process_id: data.process_id });
      onOpenChange(false);
      setGlobalSetup('');
      setProjectSetup('');
    } catch (err) {
      const isAbort = err instanceof DOMException && err.name === 'AbortError';
      toast.error(isAbort ? 'Request timed out. Please try again.' : 'Failed to save environment');
    } finally {
      setIsSubmitting(false);
    }
  };

  // When dialog opens, reset init/dirty flags so we can prefill
  useEffect(() => {
    if (open) {
      setDirtyGlobal(false);
      setDirtyProject(false);
    }
  }, [open]);

  // Prefill with latest environment scripts when editing
  useEffect(() => {
    const fetchLatest = async () => {
      if (!open || !knowledgeBaseId) return;
      setIsLoadingPrefill(true);
      try {
        const res = await fetch(`/api/repo/environments?knowledgeBaseId=${knowledgeBaseId}`);
        if (res.ok) {
          const data = await res.json();
          // Prefill on open, but do not overwrite if user already typed
          if (typeof data.global === 'string' && !dirtyGlobal) setGlobalSetup(data.global || '');
          if (typeof data.project === 'string' && !dirtyProject) setProjectSetup(data.project || '');
        }
      } catch {
        // ignore
      } finally {
        setIsLoadingPrefill(false);
      }
    };
    fetchLatest();
  }, [open, knowledgeBaseId, dirtyGlobal, dirtyProject]);

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent className="sm:max-w-[560px]">
        <AlertDialogHeader>
          <AlertDialogTitle>Environment setup</AlertDialogTitle>
        </AlertDialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="global-setup">Global setup (runner)</Label>
            <ShellEditor
              value={globalSetup}
              onChange={(v) => { setDirtyGlobal(true); setGlobalSetup(v); }}
              minHeight={180}
              placeholder="# apt-get/curl to install system packages and tools"
              forceSetValue={!dirtyGlobal}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="project-setup">Project setup (repo root)</Label>
            <ShellEditor
              value={projectSetup}
              onChange={(v) => { setDirtyProject(true); setProjectSetup(v); }}
              minHeight={140}
              placeholder="# e.g., uv sync or pnpm install"
              forceSetValue={!dirtyProject}
            />
          </div>

          <div className="text-xs text-muted-foreground space-y-1">
            <p>Runs inside Debian with Python 3 and uv preinstalled.</p>
            <p>
              Use <strong>Global setup</strong> to install system tools and dependencies (apt-get, curl). Do not clone the repository here; it will be cloned automatically using your URL/token.
            </p>
            <p>
              <strong>Project setup</strong> runs from the cloned repository root to install project dependencies (e.g., <code>uv sync</code>, <code>pnpm install</code>).
            </p>
            <p>You can fill either or both. Executed before the remote coding agent starts.</p>
          </div>

          <AlertDialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isSubmitting}>Cancel</Button>
            <Button type="submit" disabled={!canSubmit || isSubmitting}>{isSubmitting ? 'Saving...' : 'Save'}</Button>
          </AlertDialogFooter>
        </form>
      </AlertDialogContent>
    </AlertDialog>
  );
}


