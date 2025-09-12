'use client';

import { useState } from 'react';
import { AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogFooter } from '@/components/ui/alert-dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

interface EnvironmentSetupDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  knowledgeBaseId: string | undefined;
}

export function EnvironmentSetupDialog({ open, onOpenChange, knowledgeBaseId }: EnvironmentSetupDialogProps) {
  const [globalSetup, setGlobalSetup] = useState('');
  const [projectSetup, setProjectSetup] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const canSubmit = !!knowledgeBaseId && (globalSetup.trim().length > 0 || projectSetup.trim().length > 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!knowledgeBaseId) return;
    if (!canSubmit) return;

    setIsSubmitting(true);
    try {
      const res = await fetch('/api/repo/environments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          knowledgeBaseId: knowledgeBaseId,
          ...(globalSetup.trim() ? { global: globalSetup.trim() } : {}),
          ...(projectSetup.trim() ? { project: projectSetup.trim() } : {}),
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        const detail = (data && (data.detail || data.error)) || 'Failed to save environment';
        toast.error(detail);
        return;
      }

      toast.success('Environment saved');
      onOpenChange(false);
      setGlobalSetup('');
      setProjectSetup('');
    } catch (err) {
      toast.error('Failed to save environment');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent className="sm:max-w-[560px]">
        <AlertDialogHeader>
          <AlertDialogTitle>Environment setup</AlertDialogTitle>
        </AlertDialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="global-setup">Global setup (runner)</Label>
            <Textarea
              id="global-setup"
              placeholder={
                `# Runs once on the machine (e.g., install packages)\napt update && apt install -y pip3 python3-pip\ncurl -LsSf https://astral.sh/uv/install.sh | sh`
              }
              value={globalSetup}
              onChange={(e) => setGlobalSetup(e.target.value)}
              rows={5}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="project-setup">Project setup (repo root)</Label>
            <Textarea
              id="project-setup"
              placeholder={
                `# Runs in the repository root (e.g., project deps)\nuv sync`
              }
              value={projectSetup}
              onChange={(e) => setProjectSetup(e.target.value)}
              rows={4}
            />
          </div>

          <div className="text-xs text-muted-foreground">You can fill either or both. These scripts run before the remote coding agent starts.</div>

          <AlertDialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isSubmitting}>Cancel</Button>
            <Button type="submit" disabled={!canSubmit || isSubmitting}>{isSubmitting ? 'Saving...' : 'Save'}</Button>
          </AlertDialogFooter>
        </form>
      </AlertDialogContent>
    </AlertDialog>
  );
}


